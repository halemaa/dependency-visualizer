# 4 — Where this exact pattern shows up in real tools

The thing you just built — reading dependencies, finding cycles,
sorting into order — is one of the most-reused ideas in all of
software. Once you've written it once, you see it everywhere.

Here's the tour.

## Build systems — Make, Bazel, Gradle, CMake

When you type `make`, what happens?

1. Make reads your Makefile.
2. It builds a graph: "this file is built from these other files."
3. It topologically sorts that graph.
4. For each target in order, it checks: "is the output older than
   the inputs?" If yes, run the build command. If no, skip.

That's it. The famous "incremental build" feature of Make is one
graph walk.

Bazel (Google), Gradle (Android), CMake (C++) — same idea, bigger
scale. Your `dependency-visualizer` is a baby version of their core
loop.

## Package managers — npm, pip, apt, Cargo, Homebrew

When you type `pip install flask`:

1. Pip looks at `flask`'s dependencies: `Werkzeug`, `Jinja2`, `click`,
   `itsdangerous`, etc.
2. Each of THOSE has its own dependencies.
3. Pip builds the full graph.
4. Checks for cycles (sometimes the hard part).
5. Topologically sorts and installs the leaves first — things with
   no dependencies — then works upward.

When a package upgrade fails with "cannot resolve dependencies,"
it's almost always because the required graph contains a cycle or a
contradiction. The algorithm that reports this is the same algorithm
you just wrote.

## Compilers — every single one

A compiler takes your source code, parses it, builds an **AST** — an
Abstract Syntax Tree — and then walks the tree:

- Type checking: visit each node, check types based on children's types
- Code generation: walk the tree, emit machine code in post-order
- Dead-code elimination: find nodes reachable from the entry point

Your tool uses Python's own `ast` module to do the parsing. That's
the same AST that Python's bytecode compiler uses. You're literally
using the compiler's internal tool.

## Spreadsheets — Excel, Google Sheets

Every cell with a formula depends on other cells. That's a directed
graph.

When you change a cell, the spreadsheet does three things:
1. Find all cells that depend (directly or indirectly) on the one
   you changed — a graph walk.
2. Topologically sort them.
3. Recalculate in that order.

This is why spreadsheets are so fast. They don't recalculate the
whole workbook — they walk a surgical path through the dependency
graph. Same pattern.

Also: `#CIRCULAR_REF` errors? That's cycle detection firing.

## Git — the commit graph

Every commit in a Git repository points to its parent (or parents,
for merge commits). That's a directed graph — the "commit graph."

- `git log` — walks the graph backwards in topological order
- `git rebase` — replays commits on top of a different base; needs
  topological order of commits being moved
- `git merge-base` — finds the most-recent common ancestor of two
  branches by walking the graph upward from both

The reason Git can't make cycles in its commit graph: **a commit's
hash includes its parent's hash.** If A was B's parent and you tried
to make B become A's parent, A's hash would change, which would
change its content, which would change its hash — infinite loop.

Git's design makes cycles mathematically impossible, which means
`find_cycles(git_graph)` always returns `[]`.

## React, Vue, Svelte (frontend frameworks)

When React re-renders, it:

1. Figures out which components' state changed.
2. Walks the component tree (a graph).
3. Decides which descendants need to re-render.
4. Re-renders in topological order (children before parents? parents
   before children? — framework-specific, but always a topological
   walk).

The "reactivity systems" of Vue and Svelte are entirely dependency
graphs with topological sort baked in.

## Terraform, Kubernetes, CloudFormation

Infrastructure-as-code tools:

- Terraform has `terraform plan` — walks the graph of resources
  (VPC → subnet → security group → EC2 instance → load balancer),
  topologically sorts, applies in order.
- Kubernetes has readiness probes and dependency hints — the
  scheduler builds a dependency graph of pods.
- CloudFormation has "DependsOn" — explicit graph edges.

All of them: build the graph, check for cycles, topologically sort,
execute in order.

## SQL databases — foreign keys

When you define `ORDERS.customer_id → CUSTOMERS.id`, you've drawn a
graph edge. A cycle of foreign keys (A references B references A) is
usually either: (a) disallowed by the database, or (b) requires
`DEFERRABLE` constraints, which the database must detect and handle.

Cycle detection runs at schema creation time in most serious database
engines.

## Deadlock detection in operating systems

An OS maintains a "wait-for" graph: "Thread T1 wants a lock held by
T2." If T2 wants a lock held by T1, you have a cycle → deadlock.

Linux's deadlock detector, SQL Server's deadlock monitor, Java's
`jstack` thread dump analyzer — all of them run cycle detection on
a wait-for graph. Periodically, in the background, just like our
tool but on threads instead of files.

## Your Python's own import system

Python itself tracks the import graph in `sys.modules`. When you
`import foo`, Python:

1. Checks `sys.modules` — is `foo` already being imported? (Looking
   for a cycle!)
2. If yes, returns the "partially initialised" module (which is why
   some circular imports work and others don't).
3. If no, starts loading `foo`, runs its top-level code, adds it to
   `sys.modules`.

Your tool catches cycles **before** running the code. Python only
catches them when they explode at runtime. You've built a static
version of what Python does dynamically.

## The pattern, one more time

Across build systems, package managers, compilers, spreadsheets,
Git, frontend frameworks, infrastructure tools, databases, operating
systems — same three components:

1. **A directed graph** of "this depends on that"
2. **Cycle detection** to catch impossible configurations
3. **Topological sort** to decide what order to do things in

Three ideas. Every major piece of software you use has them inside
somewhere. And you just wrote the version that runs on your laptop
in 200 lines of Python.

## The one sentence to carry away

> "Any time something depends on something else, there's a directed
> graph in there. If you can model it as a graph, you've unlocked
> cycle detection, topological sort, shortest path, and reachability
> — four heavyweight tools that all run in linear time."

You don't need to memorise the algorithms. You need to notice the
pattern. The algorithms are already written. Your job is to spot the
graph.
