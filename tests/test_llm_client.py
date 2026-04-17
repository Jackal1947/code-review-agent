import pytest
from src.llm_client import LLMReviewClient, ReviewPrompt

def test_prompt_construction():
    prompt = ReviewPrompt(
        system_prompt="You are a bug hunter",
        instructions="Find bugs",
        context={"code": "def foo(): pass", "file": "test.py"}
    )
    assert "bug hunter" in prompt.system_prompt
    assert "test.py" in prompt.context_repr()