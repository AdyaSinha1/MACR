from models.schemas import Finding
from agents.base import BaseAgent


class SecurityAgent(BaseAgent):
    category = "security"

    def get_system_prompt(self) -> str:
        return (
            "You are an elite Application Security Engineer. Your job is to analyze code for security vulnerabilities "
            "such as SQL Injection, XSS, CSRF, insecure cryptographic practices, and hardcoded secrets.\n\n"
            "Example of a good finding:\n"
            "Category: security\nSeverity: critical\nCode Location: auth.py:22\n"
            "Description: 'Hardcoded API key detected in source code.'\n"
            "Explanation: 'Hardcoding secrets exposes them to source control. Use environment variables instead.'\n\n"
            "Focus entirely on SECURITY. Do not report general bugs or style issues."
        )

    def get_critique_prompt(self, current_finding: Finding) -> str:
        return (
            "You are evaluating a Security Finding reported during a code review.\n"
            f"Finding to evaluate:\n{current_finding.model_dump_json(indent=2)}\n\n"
            "Critique this finding:\n"
            "1. Is this a genuine security vulnerability or just a theoretical risk with no exploit path?\n"
            "2. Is the severity rated correctly (e.g., is a missing header really 'critical')?\n"
            "3. If it's a false positive, lower the confidence or invalidate it entirely.\n"
            "Return your critique using the expected JSON schema."
        )
