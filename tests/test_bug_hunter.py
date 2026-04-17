import pytest
from src.agents.bug_hunter import BugHunterAgent

def test_bug_hunter_instructions():
    agent = BugHunterAgent()
    instructions = agent.get_instructions()
    assert "null" in instructions.lower() or "undefined" in instructions.lower()
    assert "bug" in instructions.lower()

def test_bug_hunter_agent_type():
    agent = BugHunterAgent()
    assert agent.agent_type == "bug"
