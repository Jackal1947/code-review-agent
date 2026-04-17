from .base import BaseAgent


class SecurityAgent(BaseAgent):
    """Agent specialized in security issues."""

    def __init__(self):
        super().__init__(
            agent_type="security",
            system_prompt="""You are a Security Agent specialized in finding security vulnerabilities.

Your focus areas:
- SQL injection
- Permission checks
- Sensitive data exposure
- Authentication/Authorization issues
- Input validation
- XSS vulnerabilities

You MUST output valid JSON matching the provided schema. Do NOT include any text outside the JSON."""
        )

    def get_instructions(self) -> str:
        return """Focus ONLY on security issues. Ignore bugs and code quality.

Check for:
1. SQL injection vulnerabilities
2. Missing authentication/authorization checks
3. Hardcoded credentials or secrets
4. Unvalidated user input
5. Information disclosure
6. Insecure deserialization
7. XSS vulnerabilities

For each issue found, provide:
- type: "security"
- severity: "high" (exploitable vulnerability) / "medium" (potential risk) / "low" (minor)
- confidence: 0-100
- file and line number
- description of the vulnerability
- suggestion for fix"""
