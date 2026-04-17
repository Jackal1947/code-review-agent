"""Data models for Code Review Agent."""
from typing import TypedDict, List, Optional, Literal, Annotated
from pydantic import BaseModel, Field


def reduce_issues(left: List, right: List) -> List:
    """Reducer for combining issue lists from multiple agents."""
    return left + right


class Issue(BaseModel):
    """Single issue found in code review."""
    type: Literal["bug", "quality", "security"]
    severity: Literal["high", "medium", "low"]
    confidence: int = Field(ge=0, le=100)
    file: str
    line: int = Field(ge=1)
    description: str
    suggestion: str


class DiffChunk(BaseModel):
    """A chunk of diff for review."""
    file: str
    chunk_id: int
    code: str
    file_type: Literal["backend", "frontend", "test", "config"]


class ReviewState(TypedDict):
    """LangGraph state for review pipeline."""
    diff: str
    diff_chunks: List[DiffChunk]
    issues: Annotated[List[Issue], reduce_issues]
    final_issues: List[Issue]
    summary: Optional[str]


class ReviewResult(BaseModel):
    """Final review result."""
    issues: List[Issue]
    summary: str
    inline_comments: List[Issue]  # Only high/medium severity
