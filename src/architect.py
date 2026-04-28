"""项目架构分析模块 — 目录扫描 + AST 依赖解析。"""
import ast
import os
from pathlib import Path
from typing import List, Dict

from .models import FileArchInfo, ArchitectureContext

# 扫描时自动忽略的目录
_IGNORE_DIRS = {
    ".git", "__pycache__", ".pytest_cache", "node_modules",
    ".venv", "venv", "myenv", "env", ".tox", ".eggs",
    "dist", "build", ".idea", ".vscode", ".claude",
    "htmlcov", ".mypy_cache", ".ruff_cache",
}


def scan_directory(root_path: str, max_depth: int = 4) -> str:
    """扫描项目目录结构，返回简化的树形文本。"""
    root = Path(root_path)
    if not root.is_dir():
        return f"(目录不存在: {root_path})"

    lines = [root.name or str(root)]

    def _walk(path: Path, prefix: str, depth: int):
        if depth >= max_depth:
            return
        try:
            entries = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except PermissionError:
            return
        for i, entry in enumerate(entries):
            if entry.name.startswith(".") and entry.name not in (".env",):
                continue
            if entry.is_dir() and entry.name in _IGNORE_DIRS:
                continue
            is_last = i == len(entries) - 1
            # re-sort filtered entries to get correct last indicator
            conn = "└── " if is_last else "├── "
            lines.append(f"{prefix}{conn}{entry.name}")
            if entry.is_dir():
                ext = "    " if is_last else "│   "
                _walk(entry, prefix + ext, depth + 1)

    _walk(root, "", 0)
    return "\n".join(lines)


def parse_file_imports(file_path: str) -> List[str]:
    """解析 Python 文件的 import 语句，返回导入的模块名列表。"""
    try:
        source = Path(file_path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            dots = "." * node.level
            for alias in node.names:
                if module:
                    imports.append(f"{dots}{module}.{alias.name}")
                else:
                    imports.append(f"{dots}{alias.name}")
    return imports


def parse_file_symbols(file_path: str) -> List[str]:
    """解析 Python 文件中定义的顶层类、函数。"""
    try:
        source = Path(file_path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    symbols = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            symbols.append(f"class {node.name}")
        elif isinstance(node, ast.FunctionDef):
            symbols.append(f"def {node.name}")
        elif isinstance(node, ast.AsyncFunctionDef):
            symbols.append(f"async def {node.name}")
    return symbols


def build_dep_graph(project_root: str, changed_files: List[str]) -> ArchitectureContext:
    """对变更文件列表构建架构上下文。

    Args:
        project_root: 项目根目录。
        changed_files: 变更的文件路径列表（相对于 project_root）。

    Returns:
        ArchitectureContext 包含目录树和变更文件的依赖/符号信息。
    """
    directory_tree = scan_directory(project_root)
    changed_info: Dict[str, FileArchInfo] = {}

    for rel_path in changed_files:
        abs_path = os.path.join(project_root, rel_path)
        if not os.path.isfile(abs_path):
            continue
        if not rel_path.endswith(".py"):
            continue

        imports = parse_file_imports(abs_path)
        symbols = parse_file_symbols(abs_path)
        changed_info[rel_path] = FileArchInfo(imports=imports, symbols=symbols)

    return ArchitectureContext(
        directory_tree=directory_tree,
        changed_files=changed_info,
    )
