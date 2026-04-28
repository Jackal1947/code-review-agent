from typing import List, Dict, Any
from langgraph.graph import StateGraph, END
from .models import ReviewState, DiffChunk, Issue
from .preprocess import preprocess_diff
from .aggregator import aggregate_issues, generate_summary
from .agents.bug_hunter import BugHunterAgent
from .agents.quality import CodeQualityAgent
from .agents.security import SecurityAgent
from .skill_loader import TeamSkillLoader
from .architect import build_dep_graph

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


def architecture_node(state: ReviewState) -> Dict[str, Any]:
    """分析项目架构上下文：目录树 + 变更文件的依赖关系。"""
    chunks = state.get("diff_chunks", [])
    project_root = state.get("project_root", ".")

    # 从 diff_chunks 提取唯一的变更文件路径
    changed_files = list({chunk.file for chunk in chunks if chunk.file != "unknown"})

    if not changed_files:
        return {"arch_context": None}

    arch_context = build_dep_graph(project_root, changed_files)
    return {"arch_context": arch_context}


async def _run_agent(agent, chunks: List[DiffChunk], arch_context=None) -> List[Issue]:
    """运行单个智能体审查所有代码块。"""
    all_issues = []
    for chunk in chunks:
        context = {
            "file": chunk.file,
            "code": chunk.code,
            "chunk_id": chunk.chunk_id,
            "file_type": chunk.file_type
        }
        if arch_context:
            context["directory_tree"] = arch_context.directory_tree
            context["changed_files_arch"] = {
                f: {"imports": info.imports, "symbols": info.symbols}
                for f, info in arch_context.changed_files.items()
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
    """对所有代码块运行 Bug 查杀智能体。"""
    chunks = state.get("diff_chunks", [])
    arch_context = state.get("arch_context")
    import asyncio
    issues = asyncio.run(_run_agent(bug_agent, chunks, arch_context))
    return {"issues": issues}


def quality_agent_node(state: ReviewState) -> Dict[str, Any]:
    """对所有代码块运行代码质量智能体。"""
    chunks = state.get("diff_chunks", [])
    arch_context = state.get("arch_context")
    import asyncio
    issues = asyncio.run(_run_agent(quality_agent, chunks, arch_context))
    return {"issues": issues}


def security_agent_node(state: ReviewState) -> Dict[str, Any]:
    """对所有代码块运行安全检查智能体。"""
    chunks = state.get("diff_chunks", [])
    arch_context = state.get("arch_context")
    import asyncio
    issues = asyncio.run(_run_agent(security_agent, chunks, arch_context))
    return {"issues": issues}


def aggregator_node(state: ReviewState) -> Dict[str, Any]:
    """聚合并去重所有智能体发现的问题。"""
    all_issues = state.get("issues", [])
    final_issues = aggregate_issues(all_issues)
    summary = generate_summary(final_issues)
    return {"final_issues": final_issues, "summary": summary}


def create_review_pipeline() -> StateGraph:
    """创建 LangGraph 审查流水线。

    DAG 流向：预处理 → 架构分析 → [Bug检查, 质量检查, 安全检查] → 聚合器 → END
    """
    graph = StateGraph(ReviewState)

    # 添加节点
    graph.add_node("preprocess", preprocess_node)
    graph.add_node("architecture", architecture_node)
    graph.add_node("bug_agent", bug_agent_node)
    graph.add_node("quality_agent", quality_agent_node)
    graph.add_node("security_agent", security_agent_node)
    graph.add_node("aggregator", aggregator_node)

    # DAG 边
    graph.add_edge("preprocess", "architecture")
    graph.add_edge("architecture", "bug_agent")
    graph.add_edge("architecture", "quality_agent")
    graph.add_edge("architecture", "security_agent")
    graph.add_edge("bug_agent", "aggregator")
    graph.add_edge("quality_agent", "aggregator")
    graph.add_edge("security_agent", "aggregator")
    graph.add_edge("aggregator", END)

    graph.set_entry_point("preprocess")

    return graph.compile()
