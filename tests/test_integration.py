"""Integration tests for the code review pipeline."""
import pytest
from unittest.mock import AsyncMock, patch

from src.pipeline import create_review_pipeline
from src.models import Issue, ReviewState


@pytest.fixture
def sample_diff():
    """Sample diff for testing."""
    return """diff --git a/user.ts b/user.ts
--- a/user.ts
+++ b/user.ts
@@ -1,3 +1,4 @@
+    return 2

diff --git a/utils.ts b/utils.ts
--- a/utils.ts
+++ b/utils.ts
@@ -10,3 +10,4 @@
+    console.log("debug")

diff --git a/config.json b/config.json
--- a/config.json
+++ b/config.json
@@ -1,1 +1,2 @@
+    "new": true
"""


@pytest.fixture
def pipeline():
    """Create compiled pipeline for testing."""
    return create_review_pipeline()


def test_pipeline_integration(pipeline, sample_diff):
    """Test full pipeline from diff to review result."""
    initial_state: ReviewState = {
        "diff_chunks": [],
        "issues": [],
        "final_issues": [],
        "summary": None,
    }

    result = pipeline.invoke({**initial_state, "diff": sample_diff})

    assert len(result["diff_chunks"]) > 0
    assert isinstance(result["final_issues"], list)
    assert isinstance(result["summary"], (str, type(None)))


def test_pipeline_with_issues(pipeline):
    """Test pipeline with pre-populated issues."""
    issues = [
        Issue(
            type="bug",
            severity="high",
            confidence=90,
            file="test.ts",
            line=1,
            description="Test bug",
            suggestion="Fix it",
        )
    ]

    initial_state: ReviewState = {
        "diff_chunks": [],
        "issues": issues,
        "final_issues": [],
        "summary": None,
    }

    result = pipeline.invoke(initial_state)

    assert len(result["final_issues"]) == 1
    assert result["final_issues"][0].type == "bug"
    assert result["summary"] is not None


def test_pipeline_empty_diff(pipeline):
    """Test pipeline with empty diff."""
    initial_state: ReviewState = {
        "diff_chunks": [],
        "issues": [],
        "final_issues": [],
        "summary": None,
    }

    result = pipeline.invoke({**initial_state, "diff": ""})

    assert result["diff_chunks"] == []
    assert result["final_issues"] == []
    assert result["summary"] is not None
    assert len(result["summary"]) > 0


def test_pipeline_multiple_files(pipeline):
    """Test pipeline with multiple files in diff."""
    multi_file_diff = """diff --git a/src/app.py b/src/app.py
--- a/src/app.py
+++ b/src/app.py
@@ -1,3 +1,4 @@
+    pass

diff --git a/src/utils.py b/src/utils.py
--- a/src/utils.py
+++ b/src/utils.py
@@ -5,3 +5,4 @@
+    return True

diff --git a/tests/test_app.py b/tests/test_app.py
--- a/tests/test_app.py
+++ b/tests/test_app.py
@@ -2,1 +2,2 @@
+    assert True
"""
    initial_state: ReviewState = {
        "diff_chunks": [],
        "issues": [],
        "final_issues": [],
        "summary": None,
    }

    result = pipeline.invoke({**initial_state, "diff": multi_file_diff})

    assert len(result["diff_chunks"]) >= 3
    file_names = {chunk.file for chunk in result["diff_chunks"]}
    assert "src/app.py" in file_names
    assert "src/utils.py" in file_names
    assert "tests/test_app.py" in file_names


@pytest.mark.asyncio
async def test_full_pipeline_with_mocked_agents():
    """Test full pipeline with mocked LLM responses."""
    sample_diff = """diff --git a/test.py b/test.py
--- a/test.py
+++ b/test.py
@@ -1,3 +1,4 @@
 def hello():
-    print("hello")
+    x = None
+    return x.foo()
"""

    with patch('src.agents.base.LLMReviewClient') as mock_class:
        mock_instance = AsyncMock()
        mock_instance.review.return_value = '{"issues": [{"type": "bug", "severity": "high", "confidence": 90, "file": "test.py", "line": 3, "description": "Accessing attribute on None", "suggestion": "Add null check"}]}'
        mock_class.return_value = mock_instance

        pipeline = create_review_pipeline()
        initial_state = {"diff": sample_diff}
        result = await pipeline.ainvoke(initial_state)

        assert "final_issues" in result
        assert len(result["final_issues"]) > 0


@pytest.mark.asyncio
async def test_pipeline_with_no_issues():
    """Test pipeline when LLM finds no issues."""
    sample_diff = """diff --git a/good.py b/good.py
--- a/good.py
+++ b/good.py
@@ -1,2 +1,3 @@
 def hello():
     return "hello"
+    print("modified")
"""

    with patch('src.agents.base.LLMReviewClient') as mock_class:
        mock_instance = AsyncMock()
        mock_instance.review.return_value = '{"issues": []}'
        mock_class.return_value = mock_instance

        pipeline = create_review_pipeline()
        initial_state = {"diff": sample_diff}
        result = await pipeline.ainvoke(initial_state)

        assert "final_issues" in result
        assert "summary" in result