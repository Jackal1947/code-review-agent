"""代码审查智能体的数据模型。"""
from typing import TypedDict, List, Optional, Literal, Annotated, Dict
from pydantic import BaseModel, Field


def reduce_issues(left: List, right: List) -> List:
    """合并多个智能体产生的问题列表的归约函数。"""
    return left + right


class Issue(BaseModel):
    """代码审查中发现的单个问题。"""
    type: Literal["bug", "quality", "security"]
    severity: Literal["high", "medium", "low"]
    confidence: int = Field(ge=0, le=100)
    file: str
    line: int = Field(ge=1)
    description: str
    suggestion: str


class DiffChunk(BaseModel):
    """用于审查的差异代码块。"""
    file: str
    chunk_id: int
    code: str
    file_type: Literal["backend", "frontend", "test", "config"]


class FileArchInfo(BaseModel):
    """单个文件的架构信息。"""
    imports: List[str] = []
    symbols: List[str] = []


class ArchitectureContext(BaseModel):
    """项目架构上下文，注入到审查 Agent 中。"""
    directory_tree: str = ""
    changed_files: Dict[str, FileArchInfo] = {}


class ReviewState(TypedDict):
    """审查流水线的 LangGraph 状态。"""
    diff: str
    project_root: str
    diff_chunks: List[DiffChunk]
    issues: Annotated[List[Issue], reduce_issues]
    final_issues: List[Issue]
    summary: Optional[str]
    arch_context: Optional[ArchitectureContext]


class ReviewResult(BaseModel):
    """最终审查结果。"""
    issues: List[Issue]
    summary: str
    inline_comments: List[Issue]  # 仅包含高/中严重程度的问题
