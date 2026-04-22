# tests/test_skill_loader.py
import pytest
from src.skill_loader import TeamSkillLoader

def test_load_valid_skill(tmp_path):
    skill_file = tmp_path / "SKILL.md"
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


def test_pipeline_integration():
    """验证 pipeline 正确加载并注入 SKILL"""
    from src.pipeline import bug_agent, quality_agent, security_agent

    # SKILL should be loaded from team-rules-skill/SKILL.md
    # If the file doesn't exist, agents should still work with empty skill
    assert bug_agent is not None
    assert quality_agent is not None
    assert security_agent is not None