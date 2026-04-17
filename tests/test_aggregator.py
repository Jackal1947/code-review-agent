import pytest
from src.aggregator import aggregate_issues, deduplicate_issues, prioritize_issues


def test_deduplicate_similar_issues():
    from src.models import Issue

    issues = [
        Issue(type="bug", severity="high", confidence=90, file="user.ts", line=42,
              description="Null pointer check missing", suggestion="Add null check"),
        Issue(type="bug", severity="high", confidence=85, file="user.ts", line=42,
              description="Null pointer check missing here", suggestion="Add null check before access"),
    ]
    deduped = deduplicate_issues(issues)
    assert len(deduped) == 1


def test_prioritize_issues():
    from src.models import Issue

    issues = [
        Issue(type="bug", severity="low", confidence=50, file="a.ts", line=1,
              description="Low priority bug", suggestion="Fix it"),
        Issue(type="bug", severity="high", confidence=90, file="b.ts", line=1,
              description="High priority bug", suggestion="Fix now"),
    ]
    prioritized = prioritize_issues(issues)
    assert prioritized[0].severity == "high"
    assert prioritized[1].severity == "low"


def test_aggregate_issues():
    from src.models import Issue

    issues = [
        Issue(type="bug", severity="high", confidence=90, file="user.ts", line=42,
              description="Null pointer", suggestion="Add check"),
        Issue(type="quality", severity="medium", confidence=70, file="utils.ts", line=10,
              description="Long function", suggestion="Split it"),
    ]
    result = aggregate_issues(issues)
    assert len(result) == 2
    assert result[0].type == "bug"
