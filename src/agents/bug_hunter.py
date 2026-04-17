from .base import BaseAgent


class BugHunterAgent(BaseAgent):
    """Agent specialized in finding bugs."""

    def __init__(self):
        self._agent_type = "bug"
        self._system_prompt = """You are a Bug Hunter Agent specialized in finding critical bugs in code.

Your focus areas:
- null / undefined checks
- Boundary conditions
- Exception handling
- Concurrency issues
- Logic errors

You MUST output valid JSON matching the provided schema. Do NOT include any text outside the JSON."""

    @property
    def agent_type(self) -> str:
        return self._agent_type

    @property
    def system_prompt(self) -> str:
        return self._system_prompt

    def get_instructions(self) -> str:
        return """Focus ONLY on bugs. Ignore style and formatting issues.

Check for:
1. Missing null/undefined checks before access
2. Array index out of bounds
3. Division by zero
4. Uncaught exceptions
5. Race conditions
6. Logic errors in conditions

For each bug found, provide:
- type: "bug"
- severity: "high" (causes crash/data loss) / "medium" (incorrect behavior) / "low" (edge case)
- confidence: 0-100
- file and line number
- description of the bug
- suggestion for fix"""
