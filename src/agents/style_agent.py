from models.schemas import Finding
from agents.base import BaseAgent


class StyleAgent(BaseAgent):
    category = "style"

    def get_system_prompt(self) -> str:
        return (
            "You are an expert Python Style Reviewer. Your job is to analyze code for PEP 8 violations, "
            "poor naming conventions, lack of docstrings, and unidiomatic code.\n\n"
            "Example of a good finding:\n"
            "Category: style\nSeverity: low\nCode Location: main.py:10-12\n"
            "Description: 'Function names should be lowercase, with words separated by underscores.'\n"
            "Explanation: 'Using CamelCase for functions violates PEP 8. Rename to calculate_total.'\n\n"
            "Focus only on STYLE and READABILITY. Do not report functional bugs or security issues."
        )

    def get_critique_prompt(self, current_finding: Finding) -> str:
        return (
            "You are evaluating a Style Finding reported during a code review.\n"
            f"Finding to evaluate:\n{current_finding.model_dump_json(indent=2)}\n\n"
            "Critique this finding:\n"
            "1. Is it a genuine style violation (e.g., standard PEP 8)?\n"
            "2. Is the explanation clear and actionable?\n"
            "3. If it's a subjective false positive or minor nitpick, lower the confidence.\n"
            "Return your critique using the expected JSON schema."
        )
