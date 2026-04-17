"""Tests for code review agents."""

import pytest
from src.agents.base import agent_output_schema, BaseAgent


def test_agent_output_schema():
    """Check schema has correct structure."""
    schema = agent_output_schema()
    assert schema["type"] == "object"
    assert "properties" in schema
    assert "required" in schema
    assert "agent_type" in schema["properties"]
    assert "findings" in schema["properties"]
    assert "summary" in schema["properties"]
    assert schema["required"] == ["agent_type", "findings", "summary"]


class DummyAgent(BaseAgent):
    """Concrete implementation for testing."""

    @property
    def agent_type(self) -> str:
        return "dummy"

    @property
    def system_prompt(self) -> str:
        return "You are a dummy agent."

    def get_instructions(self) -> str:
        return "Do nothing."


def test_base_agent_prompt_structure():
    """Check prompt building."""
    agent = DummyAgent()
    context = {"file": "example.py", "content": "print('hello')"}
    prompt = agent.build_prompt(context)

    assert "You are a dummy agent." in prompt
    assert "Do nothing." in prompt
    assert "example.py" in prompt
    assert "print('hello')" in prompt
