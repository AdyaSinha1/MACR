from models.schemas import Finding
from agents.base import BaseAgent


class BugAgent(BaseAgent):
    category = "bug"

    def get_system_prompt(self) -> str:
        return (
            "You are an expert Software Engineer specializing in Bug Detection. "
            "Your job is to analyze code for logic errors, off-by-one errors, unhandled exceptions, "
            "race conditions, and edge cases.\n\n"
            "Example of a good finding:\n"
            "Category: bug\nSeverity: high\nCode Location: calc.py:45\n"
            "Description: 'Potential ZeroDivisionError when denominator is 0.'\n"
            "Explanation: 'The variable 'den' is not checked before division. Add a guard clause.'\n\n"
            "Focus strictly on functional BUGS. Do not report style or formatting issues."
        )

    def get_critique_prompt(self, current_finding: Finding) -> str:
        return (
            "You are evaluating a Bug Finding reported during a code review.\n"
            f"Finding to evaluate:\n{current_finding.model_dump_json(indent=2)}\n\n"
            "Critique this finding:\n"
            "1. Is the bug functionally reproducible based on the code provided?\n"
            "2. Is it a hallucination or false positive?\n"
            "3. If the bug is highly unlikely or the code actually handles it natively, mark is_valid as false or lower the confidence significantly.\n"
            "Return your critique using the expected JSON schema."
        )
