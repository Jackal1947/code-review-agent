import pytest
from src.pipeline import bug_agent_node, quality_agent_node, security_agent_node, create_review_pipeline, preprocess_node, aggregator_node, architecture_node
from src.models import ReviewState, DiffChunk, Issue, ArchitectureContext, FileArchInfo


def test_preprocess_node():
    from src.preprocess import preprocess_diff
    diff = """diff --git a/user.ts b/user.ts
--- a/user.ts
+++ b/user.ts
@@ -1,3 +1,4 @@
+    return 2
"""
    chunks = preprocess_diff(diff)
    state = {"diff_chunks": [], "issues": [], "final_issues": [], "summary": None, "diff": diff, "project_root": "."}
    result = preprocess_node(state)
    assert len(result["diff_chunks"]) > 0


def test_aggregator_node():
    issues = [
        Issue(type="bug", severity="high", confidence=90, file="a.ts", line=1,
              description="bug", suggestion="fix")
    ]
    state = {"diff_chunks": [], "issues": issues, "final_issues": [], "summary": None, "project_root": "."}
    result = aggregator_node(state)
    assert len(result["final_issues"]) == 1
    assert result["summary"] is not None


def test_bug_agent_node_returns_issues_list():
    state = {
        "diff": "",
        "diff_chunks": [],
        "issues": [],
        "final_issues": [],
        "summary": None,
        "project_root": ".",
    }
    result = bug_agent_node(state)
    assert "issues" in result


def test_architecture_node_extracts_file_list(tmp_path):
    """architecture_node should extract unique file paths from diff_chunks and build arch context."""
    # Create real files on disk so build_dep_graph can parse them
    (tmp_path / "main.py").write_text("import os\nfrom .utils import helper\n\nclass App:\n    pass\n")
    (tmp_path / "utils.py").write_text("def helper(): pass\n")

    chunks = [
        DiffChunk(file="main.py", chunk_id=1, code="import os", file_type="backend"),
        DiffChunk(file="main.py", chunk_id=2, code="class App:", file_type="backend"),
        DiffChunk(file="utils.py", chunk_id=1, code="def helper(): pass", file_type="backend"),
    ]
    state = {
        "diff_chunks": chunks,
        "project_root": str(tmp_path),
        "issues": [],
        "final_issues": [],
        "summary": None,
        "diff": "",
    }
    result = architecture_node(state)
    assert "arch_context" in result
    ctx = result["arch_context"]
    assert "main.py" in ctx.changed_files
    assert "utils.py" in ctx.changed_files
    assert len(ctx.changed_files["main.py"].symbols) > 0


def test_architecture_node_empty_chunks():
    """architecture_node should return None for empty diff_chunks."""
    state = {
        "diff_chunks": [],
        "project_root": ".",
        "issues": [],
        "final_issues": [],
        "summary": None,
        "diff": "",
    }
    result = architecture_node(state)
    assert result["arch_context"] is None


def test_pipeline_includes_architecture_node():
    """Verify architecture node is in the compiled pipeline."""
    pipeline = create_review_pipeline()
    # The graph should include the new architecture node
    nodes = pipeline.get_graph().nodes
    node_names = {n for n in nodes}
    assert "architecture" in node_names
    assert "preprocess" in node_names
    assert "bug_agent" in node_names
    assert "quality_agent" in node_names
    assert "security_agent" in node_names
    assert "aggregator" in node_names