"""代码审查评论格式化工具。"""
from typing import List
from src.models import Issue


def filter_inline_comments(issues: List[Issue]) -> List[Issue]:
    """筛选出高/中严重程度的问题，用于生成行内评论。"""
    return [issue for issue in issues if issue.severity in ("high", "medium")]


def format_inline_comment(issue: Issue) -> str:
    """将单个问题格式化为行内评论。"""
    severity_marker = f"[{issue.severity.upper()}]"
    return f"{severity_marker} {issue.description}（{issue.type}，置信度：{issue.confidence}%）\n建议：{issue.suggestion}"


def format_summary_comment(issues: List[Issue], summary: str) -> str:
    """将所有问题和摘要信息格式化为汇总评论。"""
    if not issues:
        return f"## 代码审查摘要\n\n{summary}\n\n未发现任何问题。"

    lines = ["## 代码审查摘要", "", summary, "", "### 发现的问题", ""]

    for issue in issues:
        severity_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(issue.severity, "⚪")
        lines.append(
            f"{severity_icon} **{issue.type.upper()}** - {issue.file}:{issue.line} "
            f"（{issue.severity}，置信度：{issue.confidence}%）"
        )
        lines.append(f"   - {issue.description}")
        lines.append(f"   - 建议：{issue.suggestion}")
        lines.append("")

    return "\n".join(lines)
