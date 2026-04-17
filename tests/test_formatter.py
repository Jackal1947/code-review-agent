import pytest
from src.formatter import format_inline_comment, format_summary_comment, filter_inline_comments
from src.models import Issue


def test_filter_inline_comments():
    issues = [
        Issue(type="bug", severity="high", confidence=90, file="user.ts", line=42,
              description="Null pointer check missing", suggestion="Add null check"),
        Issue(type="quality", severity="low", confidence=50, file="utils.ts", line=10,
              description="Long function", suggestion="Split it"),
        Issue(type="security", severity="medium", confidence=80, file="auth.py", line=5,
              description="SQL injection risk", suggestion="Use parameterized query"),
    ]
    filtered = filter_inline_comments(issues)
    assert len(filtered) == 2
    assert all(i.severity in ("high", "medium") for i in filtered)
    assert filtered[0].description == "Null pointer check missing"
    assert filtered[1].description == "SQL injection risk"


def test_filter_inline_comments_empty():
    issues = [
        Issue(type="quality", severity="low", confidence=50, file="utils.ts", line=10,
              description="Minor style issue", suggestion="Fix formatting"),
    ]
    filtered = filter_inline_comments(issues)
    assert len(filtered) == 0


def test_filter_inline_comments_all_match():
    issues = [
        Issue(type="bug", severity="high", confidence=90, file="a.ts", line=1,
              description="Bug 1", suggestion="Fix 1"),
        Issue(type="bug", severity="medium", confidence=70, file="b.ts", line=2,
              description="Bug 2", suggestion="Fix 2"),
    ]
    filtered = filter_inline_comments(issues)
    assert len(filtered) == 2


def test_format_inline_comment():
    issue = Issue(
        type="bug",
        severity="high",
        confidence=90,
        file="user.ts",
        line=42,
        description="Null pointer check missing",
        suggestion="Add null check before accessing"
    )
    result = format_inline_comment(issue)
    assert "[HIGH]" in result
    assert "Null pointer check missing" in result
    assert "bug" in result
    assert "confidence: 90%" in result
    assert "Add null check before accessing" in result


def test_format_inline_comment_medium():
    issue = Issue(
        type="quality",
        severity="medium",
        confidence=75,
        file="utils.ts",
        line=10,
        description="Long function",
        suggestion="Split into smaller functions"
    )
    result = format_inline_comment(issue)
    assert "[MEDIUM]" in result
    assert "quality" in result
    assert "Long function" in result


def test_format_summary_comment_empty():
    issues = []
    summary = "Code looks good overall"
    result = format_summary_comment(issues, summary)
    assert "Code Review Summary" in result
    assert "No issues found" in result
    assert "Code looks good overall" in result


def test_format_summary_comment_with_issues():
    issues = [
        Issue(type="bug", severity="high", confidence=90, file="user.ts", line=42,
              description="Null pointer check missing", suggestion="Add null check"),
        Issue(type="security", severity="medium", confidence=80, file="auth.py", line=5,
              description="SQL injection risk", suggestion="Use parameterized query"),
    ]
    summary = "Found critical issues that need attention"
    result = format_summary_comment(issues, summary)
    assert "Code Review Summary" in result
    assert "Found critical issues that need attention" in result
    assert "user.ts:42" in result
    assert "auth.py:5" in result
    assert "Null pointer check missing" in result
    assert "SQL injection risk" in result


def test_format_summary_comment_low_severity_omitted():
    """Low severity issues should still appear in summary (unlike inline comments)."""
    issues = [
        Issue(type="quality", severity="low", confidence=30, file="style.ts", line=1,
              description="Minor style issue", suggestion="Fix formatting"),
    ]
    result = format_summary_comment(issues, "Minor issues found")
    assert "style.ts:1" in result
    assert "Minor style issue" in result
