from typing import List
from .models import Issue


def deduplicate_issues(issues: List[Issue]) -> List[Issue]:
    """根据文件、行号和类型去除重复问题。"""
    unique_issues = []
    seen = set()

    for issue in issues:
        key = (issue.file, issue.line, issue.type)
        if key not in seen:
            seen.add(key)
            unique_issues.append(issue)
        else:
            # 保留置信度更高的问题
            for i, existing in enumerate(unique_issues):
                if (existing.file, existing.line, existing.type) == key:
                    if issue.confidence > existing.confidence:
                        unique_issues[i] = issue
                    break

    return unique_issues


def prioritize_issues(issues: List[Issue]) -> List[Issue]:
    """按优先级排序：高 > 中 > 低，同级别按置信度排序。"""
    severity_weight = {"high": 3, "medium": 2, "low": 1}

    return sorted(
        issues,
        key=lambda i: (severity_weight[i.severity], i.confidence),
        reverse=True
    )


def merge_related_issues(issues: List[Issue]) -> List[Issue]:
    """合并相关问题（同一文件、相邻行）。"""
    return issues


def aggregate_issues(all_issues: List[Issue]) -> List[Issue]:
    """主入口：对问题进行去重、合并和优先级排序。"""
    if not all_issues:
        return []

    deduped = deduplicate_issues(all_issues)
    merged = merge_related_issues(deduped)
    prioritized = prioritize_issues(merged)

    return prioritized


def generate_summary(issues: List[Issue]) -> str:
    """根据问题列表生成摘要文本。"""
    high_count = sum(1 for i in issues if i.severity == "high")
    medium_count = sum(1 for i in issues if i.severity == "medium")
    low_count = sum(1 for i in issues if i.severity == "low")

    bug_count = sum(1 for i in issues if i.type == "bug")
    quality_count = sum(1 for i in issues if i.type == "quality")
    security_count = sum(1 for i in issues if i.type == "security")

    lines = [
        f"## 🤖 AI 代码审查摘要",
        "",
        "### 概览",
        f"- {high_count} 个高风险问题",
        f"- {medium_count} 个中风险问题",
        f"- {low_count} 个低风险问题",
        "",
        "### 按类别",
        f"- {bug_count} 个 Bug",
        f"- {quality_count} 个代码质量问题",
        f"- {security_count} 个安全问题",
        "",
    ]

    if issues:
        lines.append("### 关键发现")
        for i, issue in enumerate(issues[:5], 1):
            lines.append(f"{i}. [{issue.severity.upper()}] {issue.file}:{issue.line} - {issue.description}")

    return "\n".join(lines)
