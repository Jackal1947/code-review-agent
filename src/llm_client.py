"""LLM Client for Code Review Agents."""
from typing import Any
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel


class ReviewPrompt(BaseModel):
    """Structured prompt for code review."""
    system_prompt: str
    instructions: str
    context: dict[str, Any]

    def context_repr(self) -> str:
        return f"File: {self.context.get('file', 'unknown')}\n\nCode:\n{self.context.get('code', '')}"

    def build_messages(self) -> list:
        return [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"{self.instructions}\n\n{self.context_repr()}")
        ]


class LLMReviewClient:
    """Client for calling LLM to review code."""

    def __init__(self, model: str = "claude-opus-4-5"):
        self.model = model
        self._client = ChatAnthropic(model=model)

    async def review(self, prompt: ReviewPrompt, output_schema: dict) -> dict:
        """Call LLM with structured output."""
        messages = prompt.build_messages()
        response = await self._client.ainvoke(messages)
        return response.content
