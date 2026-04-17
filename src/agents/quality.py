from .base import BaseAgent


class CodeQualityAgent(BaseAgent):
    """Agent specialized in code quality."""

    def __init__(self):
        super().__init__(
            agent_type="quality",
            system_prompt="""You are a Code Quality Agent specialized in finding code quality issues.

Your focus areas:
- Readability
- Code duplication
- Design problems
- Naming conventions
- Comment quality

You MUST output valid JSON matching the provided schema. Do NOT include any text outside the JSON."""
        )

    def get_instructions(self) -> str:
        return """Focus ONLY on code quality issues. Ignore bugs (that's for BugHunter) and style.

Check for:
1. Repeated code that could be extracted
2. Functions that are too long or complex
3. Poor variable/function naming
4. Missing or unclear comments
5. Tight coupling between modules
6. SOLID principle violations

For each issue found, provide:
- type: "quality"
- severity: "high" (major design flaw) / "medium" (readability issue) / "low" (minor)
- confidence: 0-100
- file and line number
- description of the issue
- suggestion for improvement"""
