from typing import List, Dict, Any
from langgraph.graph import StateGraph, END
from .models import ReviewState, DiffChunk, Issue
from .preprocess import preprocess_diff
from .aggregator import aggregate_issues, generate_summary
from .agents.bug_hunter import BugHunterAgent
from .agents.quality import CodeQualityAgent
from .agents.security import SecurityAgent
from .skill_loader import TeamSkillLoader

# Instantiate agents
bug_agent = BugHunterAgent()
quality_agent = CodeQualityAgent()
security_agent = SecurityAgent()

# Load team SKILL if exists
skill_loader = TeamSkillLoader()
if skill_loader.load():
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Loaded team skill: {skill_loader.name}")
    bug_agent.inject_skill_prompt(skill_loader.body)
    quality_agent.inject_skill_prompt(skill_loader.body)
    security_agent.inject_skill_prompt(skill_loader.body)


def preprocess_node(state: ReviewState) -> Dict[str, Any]:
    """将差异内容预处理为代码块。"""
    diff = state.get("diff", "")
    chunks = preprocess_diff(diff)
    return {"diff_chunks": chunks}


async def _run_agent(agent, chunks: List[DiffChunk]) -> List[Issue]:
    """运行单个智能体审查所有代码块。"""
    all_issues = []
    for chunk in chunks:
        context = {
            "file": chunk.file,
            "code": chunk.code,
            "chunk_id": chunk.chunk_id,
            "file_type": chunk.file_type
        }
        issues = await agent.review(context)
        for issue_data in issues:
            try:
                issue = Issue(**issue_data)
                all_issues.append(issue)
            except Exception:
                pass
    return all_issues


def bug_agent_node(state: ReviewState) -> Dict[str, Any]:
    """对所有代码块运行 Bug 猎手智能体。"""
    chunks = state.get("diff_chunks", [])
    import asyncio
    issues = asyncio.run(_run_agent(bug_agent, chunks))
    return {"issues": issues}


def quality_agent_node(state: ReviewState) -> Dict[str, Any]:
    """对所有代码块运行代码质量智能体。"""
    chunks = state.get("diff_chunks", [])
    import asyncio
    issues = asyncio.run(_run_agent(quality_agent, chunks))
    return {"issues": issues}


def security_agent_node(state: ReviewState) -> Dict[str, Any]:
    """对所有代码块运行安全检查智能体。"""
    chunks = state.get("diff_chunks", [])
    import asyncio
    issues = asyncio.run(_run_agent(security_agent, chunks))
    return {"issues": issues}


def aggregator_node(state: ReviewState) -> Dict[str, Any]:
    """聚合并去重所有智能体发现的问题。"""
    all_issues = state.get("issues", [])
    final_issues = aggregate_issues(all_issues)
    summary = generate_summary(final_issues)
    return {"final_issues": final_issues, "summary": summary}


def create_review_pipeline() -> StateGraph:
    """创建 LangGraph 审查流水线。

    DAG 流向：预处理 → [bug检查, 质量检查, 安全检查] → 聚合器 → END
    """
    graph = StateGraph(ReviewState)

    # 添加节点
    graph.add_node("preprocess", preprocess_node)
    graph.add_node("bug_agent", bug_agent_node)
    graph.add_node("quality_agent", quality_agent_node)
    graph.add_node("security_agent", security_agent_node)
    graph.add_node("aggregator", aggregator_node)

    # DAG 边
    graph.add_edge("preprocess", "bug_agent")
    graph.add_edge("preprocess", "quality_agent")
    graph.add_edge("preprocess", "security_agent")
    graph.add_edge("bug_agent", "aggregator")
    graph.add_edge("quality_agent", "aggregator")
    graph.add_edge("security_agent", "aggregator")
    graph.add_edge("aggregator", END)

    graph.set_entry_point("preprocess")

    return graph.compile()
