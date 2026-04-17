import pytest
from unittest.mock import AsyncMock, patch
from src.agents.bug_hunter import BugHunterAgent

@pytest.mark.asyncio
async def test_bug_hunter_review_calls_llm():
    agent = BugHunterAgent()
    context = {"file": "test.py", "code": "def foo():\n    return None\nx = foo().bar()", "chunk_id": 1}

    with patch('src.agents.base.LLMReviewClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client.review.return_value = '{"issues": []}'
        mock_client_class.return_value = mock_client

        result = await agent.review(context)
        mock_client.review.assert_called_once()