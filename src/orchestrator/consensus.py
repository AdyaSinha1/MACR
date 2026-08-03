import re
from typing import List
from structlog import get_logger

from models.schemas import Finding, SharedContext, FinalReport, Resolution
from core.llm import LLMClient

logger = get_logger()


class ConsensusEngine:
    """Resolves conflicts and overlapping findings using rule-based and LLM-based strategies."""

    def __init__(self, llm: LLMClient):
        self.llm = llm

    async def resolve(self, context: SharedContext) -> FinalReport:
        all_findings = context.get_all_findings()

        if not all_findings:
            logger.info("No findings to resolve.")
            return FinalReport(
                file_path=context.file_path,
                findings=[],
                agent_agreement=1.0,
                total_confidence=1.0,
            )

        # 1. Group findings by approximate line range
        groups = self._group_by_location(all_findings)

        resolved_findings = []

        # 2. Resolve each group
        for group in groups:
            if len(group) == 1:
                # No conflict, append directly
                resolved_findings.append(group[0])
            else:
                # Conflict exists, use LLM for semantic resolution (Batching)
                try:
                    resolved = await self._resolve_conflict(group)
                    # Include the rationale in the explanation for transparency
                    resolved.merged_finding.explanation += (
                        f"\n\n[Consensus Rationale]: {resolved.resolution_rationale}"
                    )
                    resolved_findings.append(resolved.merged_finding)
                except Exception as e:
                    logger.error(
                        "Failed to resolve conflict, falling back to all findings",
                        error=str(e),
                    )
                    resolved_findings.extend(
                        group
                    )  # Rule-based fallback: just keep them all on failure

        # Calculate metrics
        avg_confidence = (
            sum(f.confidence for f in resolved_findings) /
            len(resolved_findings)
            if resolved_findings
            else 1.0
        )

        # Agreement heuristic: high if many findings collapsed into few.
        # (Initial Findings - Final Findings) / Initial Findings
        agreement_ratio = (
            (len(all_findings) - len(resolved_findings)) / len(all_findings)
            if len(all_findings) > 0
            else 1.0
        )

        return FinalReport(
            file_path=context.file_path,
            findings=resolved_findings,
            agent_agreement=agreement_ratio,
            total_confidence=avg_confidence,
        )

    def _parse_location(self, loc: str) -> tuple[str, int, int]:
        """Extracts file, start_line, end_line. Returns (file_path, 0, 0) if unparseable."""
        match = re.search(r"(.*?):(\d+)(?:-(\d+))?", loc)
        if match:
            file_path = match.group(1).strip()
            start = int(match.group(2))
            end = int(match.group(3)) if match.group(3) else start
            return (file_path, start, end)
        return (loc, 0, 0)

    def _overlap(self, loc1: str, loc2: str, tolerance: int = 5) -> bool:
        """Checks if two locations overlap within a given tolerance."""
        file1, start1, end1 = self._parse_location(loc1)
        file2, start2, end2 = self._parse_location(loc2)
        if file1 != file2:
            return False
        if start1 == 0 and start2 == 0:
            return loc1 == loc2  # exact match fallback if parsing fails
        return max(start1, start2) <= min(end1, end2) + tolerance

    def _group_by_location(
        self, findings: List[Finding], tolerance: int = 5
    ) -> List[List[Finding]]:
        """Groups findings by overlapping code location with tolerance."""
        groups: List[List[Finding]] = []
        for finding in findings:
            placed = False
            for group in groups:
                # Check overlap against the first finding in the group
                if self._overlap(
                    finding.code_location, group[0].code_location, tolerance
                ):
                    group.append(finding)
                    placed = True
                    break
            if not placed:
                groups.append([finding])
        return groups

    async def _resolve_conflict(self, group: List[Finding]) -> Resolution:
        logger.info("Resolving conflicting findings semantically",
                    count=len(group))

        # Determine the highest severity category to use as the merged category
        severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        dominant = max(group, key=lambda f: severity_order.get(f.severity, 0))

        prompt = (
            "You are the Consensus Engine for an AI code review system.\n"
            "The following findings were reported by different agents for the exact same or overlapping code location.\n"
            "Your task is to merge them into a single, unified finding.\n\n"
            "STRICT RULES:\n"
            "1. The 'category' field in merged_finding MUST be exactly ONE of: 'style', 'bug', or 'security'. No other value is allowed.\n"
            f"2. Use category='{dominant.category}' (the most severe finding's category).\n"
            "3. Combine all descriptions and explanations into a single coherent explanation.\n"
            "4. Pick the highest severity level.\n\n"
            "Findings to merge:\n"
        )

        for idx, f in enumerate(group):
            prompt += f"--- Finding {idx+1} ---\n{f.model_dump_json(indent=2)}\n\n"

        prompt += "Provide the unified finding and a rationale for how you resolved the conflict."

        return await self.llm.generate_structured(prompt, Resolution)
