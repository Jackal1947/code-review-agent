"""Formatter for code review comments."""
from typing import List
from src.models import Issue


def filter_inline_comments(issues: List[Issue]) -> List[Issue]:
    """Filter issues to only include high/medium severity for inline comments."""
    return [issue for issue in issues if issue.severity in ("high", "medium")]


def format_inline_comment(issue: Issue) -> str:
    """Format a single issue as an inline comment."""
    severity_marker = f"[{issue.severity.upper()}]"
    return f"{severity_marker} {issue.description} ({issue.type}, confidence: {issue.confidence}%)\nSuggestion: {issue.suggestion}"


def format_summary_comment(issues: List[Issue], summary: str) -> str:
    """Format a summary comment with all issues and a summary message."""
    if not issues:
        return f"## Code Review Summary\n\n{summary}\n\nNo issues found."

    lines = ["## Code Review Summary", "", summary, "", "### Issues Found", ""]

    for issue in issues:
        severity_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(issue.severity, "⚪")
        lines.append(
            f"{severity_icon} **{issue.type.upper()}** - {issue.file}:{issue.line} "
            f"({issue.severity}, confidence: {issue.confidence}%)"
        )
        lines.append(f"   - {issue.description}")
        lines.append(f"   - Suggestion: {issue.suggestion}")
        lines.append("")

    return "\n".join(lines)
