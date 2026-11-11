"""
Build and analyse a Python project's import graph.

Walks a project folder, parses every .py file, extracts internal
imports, and builds a directed graph: "file A imports file B".

Uses DFS to detect circular imports — a bug that can cause subtle
runtime errors in Python ("ImportError: cannot import name X from
partially initialized module").
"""

from __future__ import annotations

import ast
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path


# Folders we never recurse into (noise, not part of the user's code)
SKIP_DIRS = {
    ".git", ".venv", "venv", "env", "__pycache__",
    "node_modules", ".tox", ".pytest_cache", "build", "dist",
}


@dataclass
class ImportGraph:
    """A directed graph of 'file imports file' edges."""
    edges: dict[Path, list[Path]] = field(default_factory=dict)
    root: Path = field(default_factory=Path)

    @property
    def nodes(self) -> list[Path]:
        return sorted(self.edges.keys())

    def rel(self, path: Path) -> str:
        """Relative path from the project root — nicer for display."""
        try:
            return str(path.relative_to(self.root))
        except ValueError:
            return str(path)


def _find_imports_in_file(path: Path) -> list[str]:
    """Parse a .py file and return the module names it imports."""
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except (SyntaxError, UnicodeDecodeError, OSError):
        return []

    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            # `import pkg.subpkg`
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            # `from pkg.subpkg import X`
            # X might be a submodule (pkg.subpkg.X is a file) OR a
            # name defined in pkg.subpkg's __init__. Try both and let
            # the resolver pick whichever actually exists.
            if node.module:
                for alias in node.names:
                    imports.append(f"{node.module}.{alias.name}")
                imports.append(node.module)
    return imports


def _resolve_module(module_name: str, project_root: Path) -> Path | None:
    """
    Given a module name like 'pkg.subpkg.module', try to resolve it to
    an actual .py file inside project_root.

    Returns None if it resolves to something outside the project
    (stdlib or pip-installed), which we don't track.
    """
    parts = module_name.split(".")

    # Try as a plain module: pkg/subpkg/module.py
    candidate = project_root.joinpath(*parts).with_suffix(".py")
    if candidate.is_file():
        return candidate.resolve()

    # Try as a package: pkg/subpkg/module/__init__.py
    candidate = project_root.joinpath(*parts, "__init__.py")
    if candidate.is_file():
        return candidate.resolve()

    return None


def build_graph(project_root: Path) -> ImportGraph:
    """Walk the project and build its internal import graph."""
    project_root = project_root.resolve()
    edges: dict[Path, list[Path]] = {}

    for py_file in project_root.rglob("*.py"):
        if any(part in SKIP_DIRS for part in py_file.parts):
            continue

        py_file = py_file.resolve()
        imports = _find_imports_in_file(py_file)
        seen: set[Path] = set()
        internal: list[Path] = []
        for mod in imports:
            resolved = _resolve_module(mod, project_root)
            if resolved and resolved != py_file and resolved not in seen:
                seen.add(resolved)
                internal.append(resolved)

        edges[py_file] = internal

    return ImportGraph(edges=edges, root=project_root)


def find_cycles(graph: ImportGraph) -> list[list[Path]]:
    """
    Find all circular imports using DFS with three-colour marking.

    - WHITE (0): never visited
    - GRAY  (1): currently on the DFS stack (being explored right now)
    - BLACK (2): finished exploring

    If we hit a GRAY node, we've found a cycle — the path from that
    node back to itself forms the cycle.
    """
    WHITE, GRAY, BLACK = 0, 1, 2
    colour: dict[Path, int] = defaultdict(lambda: WHITE)
    cycles: list[list[Path]] = []
    seen_cycles: set[frozenset[Path]] = set()

    def dfs(node: Path, stack: list[Path]) -> None:
        colour[node] = GRAY
        for neighbour in graph.edges.get(node, []):
            if colour[neighbour] == GRAY:
                # Cycle found: slice the stack from where the loop closes.
                try:
                    start = stack.index(neighbour)
                    cycle = stack[start:] + [neighbour]
                except ValueError:
                    continue
                key = frozenset(cycle)
                if key not in seen_cycles:
                    seen_cycles.add(key)
                    cycles.append(cycle)
            elif colour[neighbour] == WHITE:
                dfs(neighbour, stack + [neighbour])
        colour[node] = BLACK

    for node in graph.nodes:
        if colour[node] == WHITE:
            dfs(node, [node])

    return cycles


def reachable_from(graph: ImportGraph, start: Path) -> set[Path]:
    """
    All files reachable from `start` via imports (DFS).

    Useful for answering 'what would break if I changed this module?'
    """
    start = start.resolve()
    seen: set[Path] = set()
    stack: list[Path] = [start]

    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        for neighbour in graph.edges.get(node, []):
            if neighbour not in seen:
                stack.append(neighbour)

    return seen


def topological_order(graph: ImportGraph) -> list[Path] | None:
    """
    Return files in a valid dependency order: imported files come
    before the files that import them.

    Returns None if the graph has a cycle (no valid order exists).
    Uses DFS post-order.
    """
    if find_cycles(graph):
        return None

    WHITE, GRAY, BLACK = 0, 1, 2
    colour: dict[Path, int] = defaultdict(lambda: WHITE)
    order: list[Path] = []

    def dfs(node: Path) -> None:
        colour[node] = GRAY
        for neighbour in graph.edges.get(node, []):
            if colour[neighbour] == WHITE:
                dfs(neighbour)
        colour[node] = BLACK
        order.append(node)

    for node in graph.nodes:
        if colour[node] == WHITE:
            dfs(node)

    return order


def to_mermaid(graph: ImportGraph) -> str:
    """
    Emit a Mermaid flowchart that GitHub renders in markdown.

    Nodes are labelled by their relative path. IDs are sanitised so
    Mermaid's parser doesn't choke on dots or slashes.
    """
    def sanitise(path: Path) -> str:
        return (
            graph.rel(path)
            .replace("/", "_")
            .replace("\\", "_")
            .replace(".", "_")
            .replace("-", "_")
        )

    lines = ["```mermaid", "flowchart LR"]
    for node in graph.nodes:
        node_id = sanitise(node)
        label = graph.rel(node)
        lines.append(f'  {node_id}["{label}"]')
    for src, targets in graph.edges.items():
        for tgt in targets:
            lines.append(f"  {sanitise(src)} --> {sanitise(tgt)}")
    lines.append("```")
    return "\n".join(lines)
