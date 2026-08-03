import abc
from structlog import get_logger
from models.schemas import Finding, AgentCritique, SharedContext
from core.llm import LLMClient
from core.circuit_breaker import CircuitBreaker
from api.events import EventBus

logger = get_logger()


class BaseAgent(abc.ABC):
    category = "unknown"

    def __init__(self, name: str, llm: LLMClient):
        self.name = name
        self.llm = llm
        self.circuit_breaker = CircuitBreaker()
        self.max_iterations = 3

    @abc.abstractmethod
    def get_system_prompt(self) -> str:
        """Define the agent's role, rules, and few-shot examples."""

    @abc.abstractmethod
    def get_critique_prompt(self, current_finding: Finding) -> str:
        """Define how the agent should critique its own finding."""

    async def analyze(self, context: SharedContext) -> Finding:
        """Entry point for the orchestrator to trigger this agent."""
        if not self.circuit_breaker.is_allowed():
            logger.warning(
                f"Circuit breaker is open for {self.name}. Skipping analysis."
            )
            EventBus.publish_sync(
                "agent_error", {"agent": self.name, "error": "Circuit breaker open"}
            )
            return self._create_error_finding("Agent skipped due to circuit breaker.")

        try:
            logger.info(f"{self.name} starting analysis.", file=context.file_path)
            EventBus.publish_sync(
                "agent_status", {"agent": self.name, "status": "starting"}
            )
            finding = await self._run_evaluator_optimizer(context)
            EventBus.publish_sync(
                "agent_status", {"agent": self.name, "status": "complete"}
            )
            self.circuit_breaker.record_success()
            return finding

        except Exception as e:
            logger.error(f"{self.name} failed during analysis", error=str(e))
            EventBus.publish_sync("agent_error", {"agent": self.name, "error": str(e)})
            self.circuit_breaker.record_failure()
            return self._create_error_finding(f"Agent crashed: {str(e)}")

    async def _run_evaluator_optimizer(self, context: SharedContext) -> Finding:
        """The core Evaluator-Optimizer loop with a strict iteration limit."""

        # 1. Initial Generation
        prompt = f"{self.get_system_prompt()}\n\nCode to review from {context.file_path}:\n```\n{context.code_content}\n```"
        if context.past_reviews_context:
            prompt += f"\n\nHistorical Context (similar past reviews):\n{context.past_reviews_context}"

        finding = await self.llm.generate_structured(prompt, Finding)

        for iteration in range(1, self.max_iterations + 1):
            logger.info(
                f"{self.name} loop iteration {iteration}",
                current_confidence=finding.confidence,
            )
            EventBus.publish_sync(
                "agent_progress",
                {
                    "agent": self.name,
                    "iteration": iteration,
                    "confidence": finding.confidence,
                },
            )

            # Stop if confidence is high enough
            if finding.confidence > 0.85:
                logger.info(
                    f"{self.name} reached sufficient confidence ({finding.confidence}). Stopping refinement."
                )
                break

            # 2. Evaluator Step (Self-Critique)
            critique_prompt = self.get_critique_prompt(finding)
            critique = await self.llm.generate_structured(
                critique_prompt, AgentCritique
            )

            # If the critique says it's valid and boosts confidence, we can stop
            if critique.is_valid and critique.new_confidence > 0.85:
                finding.confidence = critique.new_confidence
                break

            # 3. Optimizer Step (Refinement)
            refine_prompt = (
                f"{self.get_system_prompt()}\n\n"
                f"You previously generated this finding:\n{finding.model_dump_json(indent=2)}\n\n"
                f"You then critiqued it as follows:\n{critique.model_dump_json(indent=2)}\n\n"
                f"Please address the critique and produce an updated, more accurate finding."
            )
            finding = await self.llm.generate_structured(refine_prompt, Finding)

        return finding

    def _create_error_finding(self, error_message: str) -> Finding:
        """Helper to create a 0-confidence fallback finding."""
        derived_category = (
            "style"
            if "style" in self.name.lower()
            else ("security" if "security" in self.name.lower() else "bug")
        )
        return Finding(
            agent_name=self.name,
            category=getattr(self, "category", derived_category),
            severity="low",
            code_location="N/A",
            description=error_message,
            explanation="The agent failed to complete its review.",
            confidence=0.0,
        )
