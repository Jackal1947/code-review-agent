import re
from typing import Iterator, Dict, List, Literal
from .models import DiffChunk


def split_diff_by_file(diff: str) -> Iterator[Dict]:
    """将差异内容按文件拆分为单个文件的差异。"""
    # 解析统一差异格式
    pattern = r'diff --git a/(.*) b/(.*)'
    current_file = None
    current_content = []

    for line in diff.splitlines():
        match = re.match(pattern, line)
        if match:
            if current_file:
                yield {"filename": current_file, "patch": "\n".join(current_content)}
            current_file = match.group(2)
            current_content = [line]
        elif current_file:
            current_content.append(line)

    if current_file:
        yield {"filename": current_file, "patch": "\n".join(current_content)}


def classify_file_type(filename: str) -> Literal["backend", "frontend", "test", "config"]:
    """根据文件扩展名和名称对文件类型进行分类。"""
    if any(filename.endswith(ext) for ext in [".ts", ".py", ".go", ".java", ".rs"]):
        if "test" in filename or "spec" in filename:
            return "test"
        return "backend"
    elif any(filename.endswith(ext) for ext in [".tsx", ".jsx", ".vue"]):
        return "frontend"
    elif any(filename.endswith(ext) for ext in [".json", ".yaml", ".yml", ".toml"]):
        return "config"
    elif "test" in filename or "spec" in filename:
        return "test"
    return "backend"


def split_file_by_hunks(file_diff: Dict, max_lines: int = 300) -> List[DiffChunk]:
    """将文件差异按块拆分，每块不超过 max_lines 行。"""
    chunks = []
    chunk_id = 1
    current_hunk = []
    current_lines = 0

    for line in file_diff["patch"].splitlines():
        if line.startswith("@@"):
            if current_hunk:
                chunks.append(DiffChunk(
                    file=file_diff["filename"],
                    chunk_id=chunk_id,
                    code="\n".join(current_hunk),
                    file_type=classify_file_type(file_diff["filename"])
                ))
                chunk_id += 1
                current_hunk = []
                current_lines = 0
        current_hunk.append(line)
        current_lines += 1

        if current_lines >= max_lines:
            chunks.append(DiffChunk(
                file=file_diff["filename"],
                chunk_id=chunk_id,
                code="\n".join(current_hunk),
                file_type=classify_file_type(file_diff["filename"])
            ))
            chunk_id += 1
            current_hunk = []
            current_lines = 0

    if current_hunk:
        chunks.append(DiffChunk(
            file=file_diff["filename"],
            chunk_id=chunk_id,
            code="\n".join(current_hunk),
            file_type=classify_file_type(file_diff["filename"])
        ))

    return chunks


def preprocess_diff(diff: str) -> List[DiffChunk]:
    """主入口：将差异内容拆分为代码块。"""
    all_chunks = []
    for file_diff in split_diff_by_file(diff):
        chunks = split_file_by_hunks(file_diff)
        all_chunks.extend(chunks)
    return all_chunks
