"""Tests for the dependency visualizer."""

from pathlib import Path

import pytest

from depgraph import (
    build_graph,
    find_cycles,
    reachable_from,
    to_mermaid,
    topological_order,
)


def _write(dir_: Path, name: str, content: str) -> Path:
    """Write a file; create parent dirs; return the full path."""
    p = dir_ / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return p


def test_empty_project_has_empty_graph(tmp_path):
    graph = build_graph(tmp_path)
    assert graph.nodes == []
    assert find_cycles(graph) == []


def test_file_with_no_internal_imports(tmp_path):
    _write(tmp_path, "solo.py", "x = 1\n")
    graph = build_graph(tmp_path)
    assert len(graph.nodes) == 1
    assert graph.edges[graph.nodes[0]] == []


def test_stdlib_imports_are_ignored(tmp_path):
    """Imports like 'os' or 'json' are external and shouldn't become edges."""
    _write(tmp_path, "uses_stdlib.py", "import os\nimport json\n")
    graph = build_graph(tmp_path)
    assert len(graph.nodes) == 1
    assert graph.edges[graph.nodes[0]] == []


def test_simple_import_edge(tmp_path):
    _write(tmp_path, "a.py", "from b import x\n")
    _write(tmp_path, "b.py", "x = 1\n")
    graph = build_graph(tmp_path)
    assert len(graph.nodes) == 2
    a_path = (tmp_path / "a.py").resolve()
    b_path = (tmp_path / "b.py").resolve()
    assert graph.edges[a_path] == [b_path]
    assert graph.edges[b_path] == []


def test_circular_import_detected(tmp_path):
    _write(tmp_path, "a.py", "from b import x\n")
    _write(tmp_path, "b.py", "from a import y\n")
    graph = build_graph(tmp_path)
    cycles = find_cycles(graph)
    assert len(cycles) == 1
    assert len(cycles[0]) >= 2


def test_three_way_cycle_detected(tmp_path):
    _write(tmp_path, "a.py", "from b import x\n")
    _write(tmp_path, "b.py", "from c import x\n")
    _write(tmp_path, "c.py", "from a import x\n")
    cycles = find_cycles(build_graph(tmp_path))
    assert len(cycles) == 1


def test_no_cycle_means_topological_order_exists(tmp_path):
    _write(tmp_path, "a.py", "from b import x\n")
    _write(tmp_path, "b.py", "from c import x\n")
    _write(tmp_path, "c.py", "x = 1\n")
    order = topological_order(build_graph(tmp_path))
    assert order is not None
    rels = [p.name for p in order]
    # c must come before b must come before a
    assert rels.index("c.py") < rels.index("b.py")
    assert rels.index("b.py") < rels.index("a.py")


def test_cycle_means_no_topological_order(tmp_path):
    _write(tmp_path, "a.py", "from b import x\n")
    _write(tmp_path, "b.py", "from a import x\n")
    assert topological_order(build_graph(tmp_path)) is None


def test_reachable_from(tmp_path):
    _write(tmp_path, "a.py", "from b import x\n")
    _write(tmp_path, "b.py", "from c import x\n")
    _write(tmp_path, "c.py", "x = 1\n")
    _write(tmp_path, "lonely.py", "y = 2\n")
    graph = build_graph(tmp_path)
    reached = reachable_from(graph, tmp_path / "a.py")
    names = {p.name for p in reached}
    assert "a.py" in names
    assert "b.py" in names
    assert "c.py" in names
    assert "lonely.py" not in names


def test_venv_folder_is_skipped(tmp_path):
    """Files inside .venv should not appear in the graph."""
    _write(tmp_path, "main.py", "import sys\n")
    _write(tmp_path, ".venv/lib/pkg.py", "x = 1\n")
    graph = build_graph(tmp_path)
    names = [p.name for p in graph.nodes]
    assert "main.py" in names
    assert "pkg.py" not in names


def test_mermaid_output_is_valid_format(tmp_path):
    _write(tmp_path, "a.py", "from b import x\n")
    _write(tmp_path, "b.py", "x = 1\n")
    output = to_mermaid(build_graph(tmp_path))
    assert output.startswith("```mermaid")
    assert output.endswith("```")
    assert "flowchart" in output
    assert "-->" in output
