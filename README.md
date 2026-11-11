# dependency-visualizer

Point this at any Python project folder. It reads every `.py` file,
figures out which files import which, and shows you the whole import
graph. Flags **circular imports** — a real Python bug where two files
import each other and break at runtime.

Pure Python, no dependencies. Demonstrates **graph traversal (DFS)**
and **cycle detection** on real code, not toy examples.

## See it work

Run it on this repo itself:

```bash
python visualize.py .
```

Or on any other Python project:

```bash
python visualize.py ~/projects/my-flask-app
python visualize.py . --mermaid > graph.md     # render on GitHub
python visualize.py . --check-cycles           # exit 1 if cycles exist
```

Example output on a 3-file project with a deliberate cycle:

```
Project: /home/me/cyclic_project
Python files found: 4

!! Found 1 circular import(s):
  1. a.py -> b.py -> c.py -> a.py

Import graph:
------------------------------------------------------------
  a.py
    -> b.py
  b.py
    -> c.py
  c.py
    -> a.py
  standalone.py
    (imports nothing from this project)

Summary: 4 files, 3 internal imports, 1 cycles.
```

The cycle warning is the money shot. Circular imports are easy to
write and hard to notice until something breaks in production.

## Why this is actually useful

**For your own projects:** run it periodically to catch architecture
drift. A file importing everything is a sign of poor separation.

**For code you're inheriting:** the output is a minimap of the
codebase. "Where does execution flow?" becomes a 30-second read
instead of an afternoon.

**For interviews:** "I built a tool that reads a Python project's
AST, builds its import graph, and uses DFS with three-colour marking
to detect circular dependencies" is a two-sentence summary of a
senior-level project.

## What's in the box

```
depgraph.py             core: AST parsing, graph building, DFS, cycle detection
visualize.py            CLI
tests/test_depgraph.py  11 passing tests
theory/                 written notes on graphs, DFS, cycle detection,
                        and where this pattern shows up in real tools
```

## How it works, briefly

1. **Find every .py file** in the folder (skipping `.venv`, `__pycache__`, etc.)
2. **Parse each file into an AST** using Python's built-in `ast` module.
   Walk the tree looking for `import X` and `from X import Y` statements.
3. **Resolve each imported module to a file path.** If it's inside the
   project, record an edge. If it's stdlib or pip-installed, skip.
4. **Build the graph** as `{file: [files it imports]}`.
5. **Find cycles** with DFS using three-colour marking (WHITE / GRAY /
   BLACK). If DFS visits a GRAY node, that's a cycle.
6. **Topological sort** (if cycle-free): a valid import order where
   every file's dependencies come before the file itself.

## Read the theory

1. [Imports as a graph](theory/01-imports-as-a-graph.md) — why Python
   code is naturally a directed graph
2. [DFS with three colours](theory/02-dfs-cycle-detection.md) — the
   classic cycle-detection algorithm
3. [Topological sort](theory/03-topological-sort.md) — "valid build
   order" and why it's a graph problem
4. [Where this pattern shows up](theory/04-real-world-uses.md) — build
   systems, package managers, compilers, spreadsheets

## Extending

- **Multi-language** — handle JavaScript, TypeScript, Go imports too.
  The algorithm is identical; only the parser changes.
- **Suggest where to break a cycle** — for each cycle, pick the edge
  with the fewest downstream dependents as the one to refactor.
- **Diff mode** — compare the graph before and after a PR. Flag
  when a new cycle appears.
- **Impact analysis** — "what tests should I run if I change this
  file?" Walk the reverse graph.
- **CI integration** — exit 1 on cycle means `check-cycles` can
  gate merges.

## Caveats

- Dynamic imports (`importlib.import_module(name_from_config)`) aren't
  caught — only static `import` statements.
- Relative imports (`from . import x`) are handled only for their
  module name portion; the parent-package resolution is simplified.
- `__init__.py` files that re-export (`from .child import *`) count
  as importing `.child`, which is correct but can create apparent
  cycles with aggressive re-exporting.
