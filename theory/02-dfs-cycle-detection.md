# 2 — How we find circular imports

## The problem, plainly

You have a project full of files. Some of them import each other.
Are any of them stuck in a loop — where A imports B imports C
imports A?

If there's a loop, Python will break at runtime. We want to find
these loops BEFORE a user does.

## The hand-wavy version first

Pretend you're walking through a maze that's just arrows on a map.
You start at one dot and follow arrows. If you ever return to a dot
you're currently exploring, you've found a loop.

That's actually the whole algorithm. The rest is just carefully
keeping track.

## The notebook analogy

Imagine you have a notebook with three columns:

- **"Not visited"** — dots you haven't looked at yet
- **"Currently exploring"** — dots you're in the middle of checking
  (you started here, you're following arrows outward, you haven't
  finished yet)
- **"Done"** — dots you fully explored and came back from

Start with every dot in column 1.

Pick a dot. Move it to column 2 — "Currently exploring." Now follow
each arrow out of it:

- Arrow leads to a dot in column 1 (never visited)?
  → Move IT to column 2 and go explore IT first. (Recursion.)
- Arrow leads to a dot in column 2 (currently exploring)?
  → **LOOP FOUND!** You've just drawn a path from a dot back to
  itself. That's a cycle.
- Arrow leads to a dot in column 3 (done)?
  → Already explored. Skip. Not a cycle.

When you've followed every arrow out of a dot, move it from column 2
to column 3 ("Done"). Move back to wherever you came from.

Do this for every dot until everyone is in column 3.

Any "LOOP FOUND!" moments = circular imports.

## Why the third column matters

You might think: "why do I need 'Done'? Isn't 'not column 2' the same
thing?"

No. Here's why.

Imagine this little graph:

```
    A
   / \
  B   C
   \ /
    D
```

A imports B. A imports C. Both B and C import D. Not a cycle — just
a shared dependency.

Without the "Done" column:
- Explore A. Column 2.
- Follow arrow to B. Column 2.
- Follow arrow to D. Column 2.
- D has no outgoing arrows. Move D to column 1? No! We'd re-explore D.
  Move D to column... wait, where?

With the "Done" column:
- Explore A. Column 2.
- Follow arrow to B. Column 2.
- Follow arrow to D. Column 2.
- D has no outgoing arrows. Move D to column 3 ("Done"). Back up.
- B done. Column 3. Back up.
- Now explore C. Column 2.
- Follow arrow to D. D is in column 3 (Done). **Skip** — not a cycle.
- C done. Column 3.
- A done. Column 3.

Without column 3, you'd either re-explore D (slow) or mistake "D was
visited on another branch" for a cycle (wrong).

## The code in plain words

Open `depgraph.py` and find `find_cycles`. In plain English:

```
Create a dictionary to track every dot's column.
Everyone starts in "not visited."

For each dot in the graph:
    If it's still "not visited":
        Start exploring it.

Exploring a dot means:
    Mark it "currently exploring."
    For each arrow leaving this dot:
        Where does it point?
            → A dot that's "currently exploring":
                LOOP! Record the cycle.
            → A dot that's "not visited":
                Recursively explore that one.
            → A dot that's "done":
                Skip it.
    Mark the dot "done."
```

That's literally the code, with real words instead of variable names.

## How fast is this?

Each dot gets moved to column 2 once, then to column 3 once. That's
two moves per dot. If you have N dots, that's 2N dot-operations.

For each dot, we follow its outgoing arrows. Each arrow gets looked
at once (when we explore the dot it leaves from). If there are M
arrows total, that's M arrow-operations.

Total work: 2N + M. In Big O terms, that's **O(N + M)** — linear in
the size of the graph.

You can't do better. You have to look at every dot and every arrow
at least once just to know what the graph looks like.

## A tiny worked example

Graph:
```
a → b → c → a     (circular)
     ↓
     d            (not circular)
```

Starting state: all four in column 1.

| Step | Action | Columns after |
|---|---|---|
| 1 | Start exploring `a` | a=2, b=1, c=1, d=1 |
| 2 | Follow `a → b`. Start exploring `b`. | a=2, b=2, c=1, d=1 |
| 3 | Follow `b → c`. Start exploring `c`. | a=2, b=2, c=2, d=1 |
| 4 | Follow `c → a`. `a` is in column 2 — **CYCLE!** Record it. | (unchanged) |
| 5 | `c` has no more arrows. Mark done. | a=2, b=2, c=3, d=1 |
| 6 | Follow `b → d`. Start exploring `d`. | a=2, b=2, c=3, d=2 |
| 7 | `d` has no arrows. Mark done. | a=2, b=2, c=3, d=3 |
| 8 | `b` has no more arrows. Mark done. | a=2, b=3, c=3, d=3 |
| 9 | `a` has no more arrows. Mark done. | a=3, b=3, c=3, d=3 |

One cycle found: `a → b → c → a`. The algorithm did exactly what we'd
do by hand — just systematically.

## Where this algorithm is used in real life

The "three columns" trick for finding loops in a directed graph shows
up EVERYWHERE:

- **Python / JavaScript imports.** Right here.
- **Make / Bazel build systems.** "Is there a loop in which target
  depends on which?"
- **npm / pip / apt.** "Can I install these packages without a
  dependency loop?"
- **Spreadsheets.** `A1 = B1 + 1`, `B1 = A1 + 1` → #CIRCULAR_REF
  error. Same algorithm.
- **Deadlock detection in databases.** Transaction A waiting for
  lock held by B. B waiting for lock held by A. If the algorithm
  finds a cycle, kill one of the transactions.
- **Course prerequisites.** "Can I take Advanced Networking?" —
  check that its prerequisite chain doesn't loop back to itself.

Same three columns, same loop, every time.

## What you can honestly say in an interview

> "I used depth-first search with a three-state marking — unvisited,
> currently-exploring, and done. If the search reaches a vertex
> that's 'currently-exploring,' there's a cycle, because that vertex
> is an ancestor of the current search path. It runs in linear time
> because each vertex is finalised once and each edge is traversed
> once."

That's the formal version. But now you also know what every word in
it means. That's the difference between memorising and understanding.
