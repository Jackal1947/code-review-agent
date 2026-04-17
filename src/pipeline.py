from typing import List, Dict, Any
from langgraph.graph import StateGraph, END
from .models import ReviewState, DiffChunk, Issue
from .preprocess import preprocess_diff
from .aggregator import aggregate_issues, generate_summary


def preprocess_node(state: ReviewState) -> Dict[str, Any]:
    """Preprocess the diff into chunks."""
    diff = state.get("diff", "")
    chunks = preprocess_diff(diff)
    return {"diff_chunks": chunks}


def bug_agent_node(state: ReviewState) -> Dict[str, Any]:
    """Run Bug Hunter Agent on all chunks."""
    return {"issues": []}


def quality_agent_node(state: ReviewState) -> Dict[str, Any]:
    """Run Code Quality Agent on all chunks."""
    return {"issues": []}


def security_agent_node(state: ReviewState) -> Dict[str, Any]:
    """Run Security Agent on all chunks."""
    return {"issues": []}


def aggregator_node(state: ReviewState) -> Dict[str, Any]:
    """Aggregate and deduplicate issues from all agents."""
    all_issues = state.get("issues", [])
    final_issues = aggregate_issues(all_issues)
    summary = generate_summary(final_issues)
    return {"final_issues": final_issues, "summary": summary}


def create_review_pipeline() -> StateGraph:
    """Create the LangGraph review pipeline.

    DAG flow: preprocess → [bug, quality, security] → aggregator → END
    """
    graph = StateGraph(ReviewState)

    # Add nodes
    graph.add_node("preprocess", preprocess_node)
    graph.add_node("bug_agent", bug_agent_node)
    graph.add_node("quality_agent", quality_agent_node)
    graph.add_node("security_agent", security_agent_node)
    graph.add_node("aggregator", aggregator_node)

    # DAG edges
    graph.add_edge("preprocess", "bug_agent")
    graph.add_edge("preprocess", "quality_agent")
    graph.add_edge("preprocess", "security_agent")
    graph.add_edge("bug_agent", "aggregator")
    graph.add_edge("quality_agent", "aggregator")
    graph.add_edge("security_agent", "aggregator")
    graph.add_edge("aggregator", END)

    graph.set_entry_point("preprocess")

    return graph.compile()