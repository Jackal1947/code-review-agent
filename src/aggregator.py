from typing import List
from .models import Issue


def deduplicate_issues(issues: List[Issue]) -> List[Issue]:
    """Remove duplicate issues based on file, line, and type."""
    unique_issues = []
    seen = set()

    for issue in issues:
        key = (issue.file, issue.line, issue.type)
        if key not in seen:
            seen.add(key)
            unique_issues.append(issue)
        else:
            # Keep the one with higher confidence
            for i, existing in enumerate(unique_issues):
                if (existing.file, existing.line, existing.type) == key:
                    if issue.confidence > existing.confidence:
                        unique_issues[i] = issue
                    break

    return unique_issues


def prioritize_issues(issues: List[Issue]) -> List[Issue]:
    """Sort issues by priority: high > medium > low, then by confidence."""
    severity_weight = {"high": 3, "medium": 2, "low": 1}

    return sorted(
        issues,
        key=lambda i: (severity_weight[i.severity], i.confidence),
        reverse=True
    )


def merge_related_issues(issues: List[Issue]) -> List[Issue]:
    """Merge issues that are related (same file, close lines)."""
    return issues


def aggregate_issues(all_issues: List[Issue]) -> List[Issue]:
    """Main entry point: deduplicate, merge, and prioritize issues."""
    if not all_issues:
        return []

    deduped = deduplicate_issues(all_issues)
    merged = merge_related_issues(deduped)
    prioritized = prioritize_issues(merged)

    return prioritized


def generate_summary(issues: List[Issue]) -> str:
    """Generate summary text from issues."""
    high_count = sum(1 for i in issues if i.severity == "high")
    medium_count = sum(1 for i in issues if i.severity == "medium")
    low_count = sum(1 for i in issues if i.severity == "low")

    bug_count = sum(1 for i in issues if i.type == "bug")
    quality_count = sum(1 for i in issues if i.type == "quality")
    security_count = sum(1 for i in issues if i.type == "security")

    lines = [
        f"## 🤖 AI Code Review Summary",
        "",
        "### Overview",
        f"- {high_count} high risk issue{'s' if high_count != 1 else ''}",
        f"- {medium_count} medium issue{'s' if medium_count != 1 else ''}",
        f"- {low_count} low risk issue{'s' if low_count != 1 else ''}",
        "",
        "### By Category",
        f"- {bug_count} bug{'s' if bug_count != 1 else ''}",
        f"- {quality_count} quality issue{'s' if quality_count != 1 else ''}",
        f"- {security_count} security issue{'s' if security_count != 1 else ''}",
        "",
    ]

    if issues:
        lines.append("### Key Findings")
        for i, issue in enumerate(issues[:5], 1):
            lines.append(f"{i}. [{issue.severity.upper()}] {issue.file}:{issue.line} - {issue.description}")

    return "\n".join(lines)
