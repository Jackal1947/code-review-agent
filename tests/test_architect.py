"""Tests for architecture analysis module."""
import os
import tempfile
from pathlib import Path

import pytest

from src.architect import (
    scan_directory,
    parse_file_imports,
    parse_file_symbols,
    build_dep_graph,
)
from src.models import ArchitectureContext


class TestScanDirectory:
    """Tests for scan_directory()."""

    def test_returns_tree_for_valid_dir(self, tmp_path: Path):
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("print('hello')")
        (tmp_path / "src" / "utils").mkdir()
        (tmp_path / "src" / "utils" / "helpers.py").write_text("def foo(): pass")
        (tmp_path / "tests").mkdir()

        tree = scan_directory(str(tmp_path))

        assert "src" in tree
        assert "main.py" in tree
        assert "utils" in tree
        assert "helpers.py" in tree
        assert "tests" in tree

    def test_ignores_hidden_and_venv_dirs(self, tmp_path: Path):
        (tmp_path / ".git").mkdir()
        (tmp_path / "__pycache__").mkdir()
        (tmp_path / "node_modules").mkdir()
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "app.py").write_text("")

        tree = scan_directory(str(tmp_path))

        assert ".git" not in tree
        assert "__pycache__" not in tree
        assert "node_modules" not in tree
        assert "src" in tree
        assert "app.py" in tree

    def test_returns_error_for_missing_dir(self):
        tree = scan_directory("/nonexistent/path")
        assert "不存在" in tree


class TestParseFileImports:
    """Tests for parse_file_imports()."""

    def test_parses_import_statements(self, tmp_path: Path):
        f = tmp_path / "mod.py"
        f.write_text("""import os
import sys
from pathlib import Path
from .models import Issue, ReviewState
from typing import List, Optional
""")
        imports = parse_file_imports(str(f))
        assert "os" in imports
        assert "sys" in imports
        assert "pathlib.Path" in imports
        assert ".models.Issue" in imports
        assert ".models.ReviewState" in imports
        assert "typing.List" in imports
        assert "typing.Optional" in imports

    def test_handles_relative_imports(self, tmp_path: Path):
        f = tmp_path / "mod.py"
        f.write_text("""from . import base
from ..utils import helper
""")
        imports = parse_file_imports(str(f))
        assert ".base" in imports
        assert "..utils.helper" in imports

    def test_returns_empty_on_syntax_error(self, tmp_path: Path):
        f = tmp_path / "bad.py"
        f.write_text("this is not valid python ======")
        imports = parse_file_imports(str(f))
        assert imports == []

    def test_returns_empty_on_missing_file(self):
        imports = parse_file_imports("/nonexistent/file.py")
        assert imports == []


class TestParseFileSymbols:
    """Tests for parse_file_symbols()."""

    def test_parses_classes_and_functions(self, tmp_path: Path):
        f = tmp_path / "mod.py"
        f.write_text("""class Foo:
    def method(self):
        pass

def bar():
    pass

async def baz():
    pass

CONSTANT = 42
""")
        symbols = parse_file_symbols(str(f))
        assert "class Foo" in symbols
        assert "def bar" in symbols
        assert "async def baz" in symbols

    def test_returns_empty_on_syntax_error(self, tmp_path: Path):
        f = tmp_path / "bad.py"
        f.write_text("<<<<broken>>>>")
        symbols = parse_file_symbols(str(f))
        assert symbols == []


class TestBuildDepGraph:
    """Tests for build_dep_graph()."""

    def test_builds_context_for_multiple_files(self, tmp_path: Path):
        # Create a mini project
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("""import os
from .utils import helper

class App:
    def run(self):
        pass
""")
        (tmp_path / "src" / "utils.py").write_text("""def helper():
    pass
""")

        changed_files = ["src/main.py", "src/utils.py"]
        ctx = build_dep_graph(str(tmp_path), changed_files)

        assert isinstance(ctx, ArchitectureContext)
        assert len(ctx.directory_tree) > 0
        assert "src/main.py" in ctx.changed_files
        assert "src/utils.py" in ctx.changed_files
        assert ".utils.helper" in ctx.changed_files["src/main.py"].imports
        assert "class App" in ctx.changed_files["src/main.py"].symbols

    def test_skips_non_python_files(self, tmp_path: Path):
        (tmp_path / "config.json").write_text('{"key": "value"}')
        (tmp_path / "app.py").write_text("import os")
        (tmp_path / "app.py").write_text("import os")

        # app.py was written twice, but the content is the same
        changed_files = ["config.json", "app.py"]
        ctx = build_dep_graph(str(tmp_path), changed_files)

        assert "config.json" not in ctx.changed_files
        assert "app.py" in ctx.changed_files

    def test_handles_missing_files(self, tmp_path: Path):
        changed_files = ["does_not_exist.py"]
        ctx = build_dep_graph(str(tmp_path), changed_files)

        assert ctx.changed_files == {}
        assert len(ctx.directory_tree) > 0
