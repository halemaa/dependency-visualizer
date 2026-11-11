# 3 — The "what order should I do things?" problem

## A tiny real problem

Say you're making tea with milk. The steps are:

1. Boil water
2. Pour water into cup
3. Add tea bag
4. Steep
5. Add milk
6. Stir
7. Drink

Some steps HAVE to come before others. You can't stir before adding
tea. You can't drink before stirring. But some steps are flexible —
you could boil water BEFORE getting your mug out, or after. Doesn't
matter.

**Finding a valid order to do things when some things must come
before others** is called a **topological sort**.

## The graph version

Draw a dot for each step. Draw an arrow from step X to step Y if X
MUST happen before Y:

```
boil_water ──→ pour_water ──→ add_tea_bag ──→ steep ──→ stir ──→ drink
                                                          ▲
                                add_milk ────────────────┘
```

Now the question becomes: "give me a line of dots such that every
arrow points forwards."

## Why this is a graph problem

Every situation where "things depend on other things" has this shape:

- **Building a software project.** Compile library A before program
  B that uses A. Package manager: install the dependency before
  installing the thing that depends on it.
- **Course prerequisites.** Take "Calculus 1" before "Calculus 2".
- **Cooking a complex meal.** Chop vegetables before frying them.
  Make the sauce before the pasta is ready to serve.
- **Project plans.** Finish the research before writing the report.

All of them: a dot per task, an arrow from "must happen first" to
"must happen second," and the question: "what's a valid order?"

## Python imports are one of these

When Python loads your project, it doesn't magically know the right
order to load files. It figures it out by following imports: when
`main.py` says `from helpers import hello`, Python loads
`helpers.py` BEFORE finishing `main.py`.

That's Python doing its own topological sort, on the fly. Our tool
computes the same order explicitly, so you can see what it is.

## The algorithm, in plain words

Here's the honest part: **we already wrote it in the cycle-detection
chapter.** Topological sort is the same DFS, with one tiny addition.

Remember the three columns — "not visited," "currently exploring,"
"done"? Here's the trick:

**When a dot moves to "done," append it to a list.**

When the whole thing is finished, the list is your topological
order — **reversed**.

Why reversed? Because DFS moves a dot to "done" only AFTER exploring
everything it points to. So the first dot to get "done" is one with
no outgoing arrows — a leaf, something nothing depends on. The LAST
dot to get "done" is one at the top of everything.

Reverse that list, and you've got: "do the things with nothing to
wait for first, then the things that depend on those, and so on."

## A walked-through example

Tiny project:

```
a.py: imports b.py
b.py: imports c.py
c.py: (no internal imports)
```

Graph:
```
a.py → b.py → c.py
```

Walk:

1. Start DFS on `a.py`. Mark it "exploring."
2. Follow arrow to `b.py`. Mark "exploring."
3. Follow arrow to `c.py`. Mark "exploring."
4. `c.py` has no outgoing arrows. Done. **Append to list: [c.py]**
5. Back up to `b.py`. All its arrows explored. Done.
   **Append to list: [c.py, b.py]**
6. Back up to `a.py`. All its arrows explored. Done.
   **Append to list: [c.py, b.py, a.py]**

Final order: `c.py → b.py → a.py`. Which reads as: "load c first,
then b, then a." Exactly right. Dependencies come before the files
that depend on them.

## The one condition

Topological sort ONLY works if there are no cycles.

If `a` depends on `b` and `b` depends on `a`, there is NO valid
order. One of them has to come first, but then the other one has to
come before it, but then the first one has to come before THAT. Dead
end.

That's why our tool checks for cycles FIRST, and only produces a
topological order if there are none. If you look at `topological_order`
in `depgraph.py`:

```python
def topological_order(graph):
    if find_cycles(graph):
        return None     # No valid order exists.
    ...
```

Honest about the limit.

## Where you've seen this already (even if you didn't know it)

**Make / Bazel.** When you type `make`, it reads your Makefile,
builds a graph of "this target depends on this target," topologically
sorts, and compiles things in the right order.

**npm install / pip install.** Builds a dependency graph of packages,
topologically sorts, installs leaves first.

**Build pipelines in CI/CD.** "Run tests after build. Run deploy
after tests pass." Just a topological sort of pipeline stages.

**React / Vue component updates.** When state changes, the framework
topologically sorts components that need re-rendering.

**Course registration systems.** Universities compute which courses
you CAN take this semester based on which prerequisites you've
cleared. Topological sort.

**Spreadsheets.** When you change a cell, Excel recomputes dependent
cells in topological order so each one sees fresh values.

Same algorithm. Same three-column DFS, with one line added to record
the finish order.

## The interview-ready sentence

> "Topological sort of a directed acyclic graph. Run DFS and record
> the order vertices are finalised. Reverse that order, and you've
> got a valid ordering: every edge goes forward. Fails cleanly if
> there's a cycle — because by definition no topological order can
> exist in that case."

Short. Correct. Shows you know where it comes from.
