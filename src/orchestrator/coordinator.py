import asyncio
from structlog import get_logger

from models.schemas import SharedContext, FinalReport
from agents.style_agent import StyleAgent
from agents.bug_agent import BugAgent
from agents.security_agent import SecurityAgent
from core.llm import LLMClient
from orchestrator.consensus import ConsensusEngine
from memory.faiss_store import FaissMemoryStore
from api.events import EventBus

logger = get_logger()


class ReviewCoordinator:
    """Orchestrates the multi-agent code review workflow."""

    def __init__(self, memory_store: FaissMemoryStore = None):
        self.llm = LLMClient()
        self.consensus_engine = ConsensusEngine(llm=self.llm)
        self.memory_store = memory_store

        # Instantiate agents
        self.agents = [
            StyleAgent(name="StyleAgent", llm=self.llm),
            BugAgent(name="BugAgent", llm=self.llm),
            SecurityAgent(name="SecurityAgent", llm=self.llm),
        ]

    async def review_file(self, file_path: str, code_content: str) -> FinalReport:
        """Runs a concurrent multi-agent review on a single file."""
        logger.info("Starting multi-agent review", file_path=file_path)
        EventBus.publish_sync("review_status", {"status": "initializing"})

        past_context = ""
        if self.memory_store:
            EventBus.publish_sync(
                "review_status", {"status": "retrieving_memory"})
            # Truncate code content to first 1000 chars to avoid diluting the semantic embedding
            similar_reviews = self.memory_store.retrieve_similar(
                code_content[:1000], k=2
            )
            if similar_reviews:
                past_context = "\n---\n".join([r["summary"]
                                              for r in similar_reviews])
                logger.info(
                    "Retrieved past reviews for context", count=len(similar_reviews)
                )
                EventBus.publish_sync(
                    "memory_context", {"count": len(similar_reviews)})

        # Initialize the immutable blackboard
        context = SharedContext(
            file_path=file_path,
            code_content=code_content,
            past_reviews_context=past_context,
            style_findings=[],
            bug_findings=[],
            security_findings=[],
        )

        # Run all agents in parallel without blocking the event loop
        EventBus.publish_sync("review_status", {"status": "analyzing"})
        tasks = [agent.analyze(context) for agent in self.agents]
        findings = await asyncio.gather(*tasks)

        # Populate the blackboard with the results
        for finding in findings:
            if finding.confidence == 0.0:
                logger.debug(
                    f"Skipping finding from {finding.agent_name} due to 0 confidence (likely error)."
                )
                continue

            if finding.category == "style":
                context.style_findings.append(finding)
            elif finding.category == "bug":
                context.bug_findings.append(finding)
            elif finding.category == "security":
                context.security_findings.append(finding)
            else:
                logger.warning(
                    f"Unknown finding category '{finding.category}'. Defaulting to bug."
                )
                context.bug_findings.append(finding)

        logger.info(
            "Agent analysis complete", total_findings=len(context.get_all_findings())
        )

        # Pass the populated context to the consensus engine to resolve overlaps and generate the final report
        EventBus.publish_sync("review_status", {"status": "consensus"})
        final_report = await self.consensus_engine.resolve(context)

        if self.memory_store:
            self.memory_store.store_review(final_report)

        EventBus.publish_sync("review_complete", final_report.model_dump())
        return final_report
