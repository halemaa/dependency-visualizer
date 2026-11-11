"""
Scan a Python project and report its import graph.

Usage:
    python visualize.py .                         # current folder
    python visualize.py path/to/project
    python visualize.py . --mermaid > graph.md    # render in a markdown doc
    python visualize.py . --check-cycles          # exits 1 if cycles found
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from depgraph import build_graph, find_cycles, to_mermaid, topological_order


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Visualize and analyse Python import graphs.",
    )
    parser.add_argument(
        "project", nargs="?", default=".",
        help="path to the Python project root (default: current folder)",
    )
    parser.add_argument(
        "--mermaid", action="store_true",
        help="output a Mermaid flowchart instead of the text report",
    )
    parser.add_argument(
        "--check-cycles", action="store_true",
        help="exit with status 1 if any circular imports are found",
    )
    args = parser.parse_args()

    root = Path(args.project).expanduser().resolve()
    if not root.is_dir():
        print(f"Not a directory: {root}", file=sys.stderr)
        return 2

    graph = build_graph(root)

    if args.mermaid:
        print(to_mermaid(graph))
        return 0

    # Text report
    print(f"Project: {root}")
    print(f"Python files found: {len(graph.nodes)}")
    print()

    cycles = find_cycles(graph)
    if cycles:
        print(f"!! Found {len(cycles)} circular import(s):")
        for i, cycle in enumerate(cycles, 1):
            chain = " -> ".join(graph.rel(p) for p in cycle)
            print(f"  {i}. {chain}")
        print()

    print("Import graph:")
    print("-" * 60)
    total_edges = 0
    for node in graph.nodes:
        targets = graph.edges.get(node, [])
        total_edges += len(targets)
        if not targets:
            print(f"  {graph.rel(node)}")
            print(f"    (imports nothing from this project)")
        else:
            print(f"  {graph.rel(node)}")
            for target in targets:
                print(f"    -> {graph.rel(target)}")
    print()
    print(f"Summary: {len(graph.nodes)} files, {total_edges} internal imports, {len(cycles)} cycles.")

    order = topological_order(graph)
    if order:
        print()
        print("Valid import order (dependencies first):")
        for path in order:
            print(f"  - {graph.rel(path)}")

    if args.check_cycles and cycles:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
