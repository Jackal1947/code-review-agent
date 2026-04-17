"""Base agent abstract class for code review."""

from abc import ABC, abstractmethod
from typing import Any


def agent_output_schema() -> dict[str, Any]:
    """Return the JSON schema for agent output."""
    return {
        "type": "object",
        "properties": {
            "agent_type": {"type": "string"},
            "findings": {
                "type": "array",
                "items": {"type": "string"}
            },
            "summary": {"type": "string"},
        },
        "required": ["agent_type", "findings", "summary"],
    }


class BaseAgent(ABC):
    """Abstract base class for code review agents."""

    @property
    @abstractmethod
    def agent_type(self) -> str:
        """Return the type identifier for this agent."""
        pass

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Return the system prompt for this agent."""
        pass

    @abstractmethod
    def get_instructions(self) -> str:
        """Return the instructions for this agent."""
        pass

    def build_prompt(self, context: dict[str, Any]) -> str:
        """Build a prompt from the given context."""
        instructions = self.get_instructions()
        return f"{self.system_prompt}\n\nInstructions: {instructions}\n\nContext: {context}"

    async def review(self, context: dict[str, Any]) -> list[str]:
        """Review the given context and return findings."""
        return []
