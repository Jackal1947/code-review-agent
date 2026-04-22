# tests/test_skill_loader.py
import pytest
from src.skill_loader import TeamSkillLoader

def test_load_valid_skill(tmp_path):
    skill_file = tmp_path / "default.md"
    skill_file.write_text("""---
name: test-skill
description: Test description
---

# Test Skill Body

This is test content.
""")
    loader = TeamSkillLoader(skill_path=str(skill_file))
    result = loader.load()
    assert result is True
    assert loader.name == "test-skill"
    assert loader.description == "Test description"
    assert "Test Skill Body" in loader.body

def test_load_nonexistent_skill():
    loader = TeamSkillLoader(skill_path="nonexistent/path/default.md")
    result = loader.load()
    assert result is False
    assert loader.is_loaded is False

def test_skill_not_loaded_initially():
    loader = TeamSkillLoader()
    assert loader.is_loaded is False

def test_agent_inject_skill():
    from src.agents.bug_hunter import BugHunterAgent

    agent = BugHunterAgent()
    original_prompt = agent.system_prompt

    skill_content = "Team skill content"
    agent.inject_skill_prompt(skill_content)

    # Verify skill was injected
    combined = agent.system_prompt
    assert "Team skill content" in combined
    assert "---" in combined  # Separator should exist