"""Tests for code review agents."""

import pytest
from src.agents.base import agent_output_schema, BaseAgent
from src.agents.bug_hunter import BugHunterAgent
from src.agents.quality import CodeQualityAgent
from src.agents.security import SecurityAgent


class DummyAgent(BaseAgent):
    """Concrete implementation for testing."""

    def __init__(self):
        super().__init__(agent_type="dummy", system_prompt="You are a dummy agent.")

    @property
    def agent_type(self) -> str:
        return self._agent_type

    @property
    def system_prompt(self) -> str:
        return self._system_prompt

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


def test_bug_hunter_agent_properties():
    agent = BugHunterAgent()
    assert agent.agent_type == "bug"
    assert "Bug" in agent.system_prompt


def test_quality_agent_init():
    agent = CodeQualityAgent()
    assert agent.agent_type == "quality"


def test_security_agent_init():
    agent = SecurityAgent()
    assert agent.agent_type == "security"
