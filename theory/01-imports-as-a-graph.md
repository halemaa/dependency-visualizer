# 1 — Your code is a graph (yes, really)

## Start with what a "graph" actually is

Forget any CS class you had on this. A graph is just two things:

- **Dots** (called nodes or vertices) — the "things"
- **Lines** (called edges) — connections between them

That's it. Draw some dots. Draw lines between the ones that are
connected. You just made a graph.

Real-life graphs:

- **Your WhatsApp contacts.** Each person is a dot. A line between
  two people means they've chatted.
- **The roads in your city.** Each intersection is a dot. Each road
  is a line.
- **Your family tree.** Each person is a dot. A line connects a
  parent to a child.

## Now the twist — arrows matter

Some connections only go one way.

On Instagram, you can follow someone who doesn't follow you back.
That's an **arrow**, not just a line. The arrow goes from you to them.

A graph where connections have arrows is called a **directed graph**.
It matters because the direction tells you something.

- Your family tree: parent → child. Child-to-parent is a different
  relationship.
- Twitter follows: you → celebrity. Not the other way.
- Python imports: `a.py` imports `b.py` → arrow from `a.py` to `b.py`.

## Your Python project is a directed graph

Here's the "wait, what?" moment.

Every `.py` file in your project is a dot. Every `import` statement
is an arrow.

Look at a tiny project:

```
main.py           →   from service import run
service.py        →   from database import save
service.py        →   from helpers import hello
database.py       →   from helpers import hello
helpers.py        →   (imports nothing)
```

Draw that:

```
      main.py
        │
        ▼
     service.py
     │       │
     ▼       ▼
database.py  helpers.py
     │           ▲
     └───────────┘
```

Arrows point *from the file doing the importing* to *the file being
imported*. Four dots. Five arrows. That's your project's graph.

## Why bothering to see it this way matters

Once your code is a graph, you can ask real questions about it:

**"Does `main.py` depend on `helpers.py`?"**
→ Can I walk from `main.py` to `helpers.py` by following arrows? Yes.

**"What breaks if I change `helpers.py`?"**
→ Everything that has a path TO `helpers.py`. (In this example: all
four other files.)

**"Do we have a circular import?"** (The scary one.)
→ Is there a loop in the arrows? Can I start somewhere and follow
arrows all the way back to where I started?

These are the exact questions `dependency-visualizer` answers.

## What a "circular import" actually is

Imagine `a.py` has `from b import X`, and `b.py` has `from a import Y`.

Draw it:

```
a.py ──> b.py
 ▲        │
 └────────┘
```

A loop. They depend on each other.

**Why that's a problem in Python:** Python runs a file the first
time it's imported. Think about what happens when you run `a.py`:

1. Python starts loading `a.py`
2. First line: `from b import X`. Python pauses `a.py` and loads `b.py`.
3. First line of `b.py`: `from a import Y`. Python sees "wait, I'm
   already in the middle of loading `a.py`."
4. Python does its best. If `Y` was defined above the `from b` line,
   fine. If it wasn't yet (because we hadn't gotten there), you get:
   > *"ImportError: cannot import name 'Y' from partially initialized
   > module 'a'"*

This is a real bug that breaks real apps. And it's silent — the code
looks fine, until someone runs it in the wrong order and it explodes.

That's why finding cycles in your import graph matters. Not an
academic exercise — a working bug detector.

## How your code stores the graph

Open `depgraph.py` and look for this line:

```python
edges: dict[Path, list[Path]] = field(default_factory=dict)
```

That's the whole graph. A dict. The keys are files. The values are
lists of other files that get imported.

```python
edges = {
    "main.py":     ["service.py"],
    "service.py":  ["database.py", "helpers.py"],
    "database.py": ["helpers.py"],
    "helpers.py":  [],
}
```

That's it. Everything else in the code — cycle detection, topological
sort, reachability — is just a loop that walks this dict.

**A graph in code is almost always "a dict with lists inside it."**
If you understand that, you understand what a graph data structure
actually is.

## The habit to build

Every time you see a problem about **things that depend on other
things**, ask yourself: *"can I model this as a graph?"*

If yes — and it almost always is — you've unlocked a whole box of
pre-made tools: cycle detection, shortest path, topological sort,
connected components. You don't invent them. You just apply them.

Python imports are a graph. Build systems are a graph. Package
dependencies are a graph. Spreadsheet cells are a graph. Git commits
are a graph. Database foreign keys are a graph. Once you see the
pattern, you see it everywhere.
