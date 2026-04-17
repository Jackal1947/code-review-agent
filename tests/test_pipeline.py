import pytest
from src.pipeline import bug_agent_node, quality_agent_node, security_agent_node, create_review_pipeline, preprocess_node, aggregator_node
from src.models import ReviewState, DiffChunk, Issue


def test_preprocess_node():
    from src.preprocess import preprocess_diff
    diff = """diff --git a/user.ts b/user.ts
--- a/user.ts
+++ b/user.ts
@@ -1,3 +1,4 @@
+    return 2
"""
    chunks = preprocess_diff(diff)
    state = {"diff_chunks": [], "issues": [], "final_issues": [], "summary": None, "diff": diff}
    result = preprocess_node(state)
    assert len(result["diff_chunks"]) > 0


def test_aggregator_node():
    issues = [
        Issue(type="bug", severity="high", confidence=90, file="a.ts", line=1,
              description="bug", suggestion="fix")
    ]
    state = {"diff_chunks": [], "issues": issues, "final_issues": [], "summary": None}
    result = aggregator_node(state)
    assert len(result["final_issues"]) == 1
    assert result["summary"] is not None


def test_bug_agent_node_returns_issues_list():
    state = ReviewState(
        diff="",
        diff_chunks=[],
        issues=[],
        final_issues=[],
        summary=None
    )
    result = bug_agent_node(state)
    assert "issues" in result