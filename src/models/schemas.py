from typing import List, Literal
from pydantic import BaseModel, Field


class Finding(BaseModel):
    """Represents a single issue found by an agent during code review."""

    agent_name: str = Field(
        description="The name of the agent reporting the finding (e.g., StyleAgent, BugAgent)"
    )
    category: Literal["style", "bug", "security"] = Field(
        description="Category of the finding"
    )
    severity: Literal["low", "medium", "high", "critical"] = Field(
        description="Severity of the issue"
    )
    code_location: str = Field(
        description="File path and line numbers (e.g., src/main.py:10-15)"
    )
    description: str = Field(description="Detailed description of the issue")
    explanation: str = Field(
        description="Explanation of why this is an issue and how to fix it"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score of the finding between 0.0 and 1.0",
    )


class AgentCritique(BaseModel):
    """Represents an agent's self-critique during the Evaluator-Optimizer loop."""

    is_valid: bool = Field(
        description="Whether the initial finding holds up to scrutiny"
    )
    critique: str = Field(
        description="Critique of the initial finding, identifying false positives or lack of clarity"
    )
    suggested_improvements: str = Field(
        description="Suggestions to improve the finding's accuracy and explanation"
    )
    new_confidence: float = Field(
        ge=0.0, le=1.0, description="Adjusted confidence score after critique"
    )


class SharedContext(BaseModel):
    """The immutable blackboard where agents post their findings."""

    file_path: str = Field(description="Path to the file being reviewed")
    code_content: str = Field(description="The source code being reviewed")
    past_reviews_context: str = Field(
        default="", description="Context from similar past reviews"
    )
    style_findings: List[Finding] = Field(default_factory=list)
    bug_findings: List[Finding] = Field(default_factory=list)
    security_findings: List[Finding] = Field(default_factory=list)

    def get_all_findings(self) -> List[Finding]:
        return self.style_findings + self.bug_findings + self.security_findings


class Resolution(BaseModel):
    """Represents a conflict resolution decision by the ConsensusEngine."""

    merged_finding: Finding = Field(
        description="The final unified finding after merging overlaps/conflicts"
    )
    resolution_rationale: str = Field(
        description="Explanation of how the conflict was resolved"
    )


class FinalReport(BaseModel):
    """The final generated report after consensus."""

    file_path: str
    findings: List[Finding] = Field(
        description="List of finalized and resolved findings"
    )
    agent_agreement: float = Field(
        description="Score indicating how much agents agreed on findings (0.0 to 1.0)"
    )
    total_confidence: float = Field(
        description="Overall confidence score of the report (0.0 to 1.0)"
    )
