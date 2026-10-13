# refinement.md — sympy__sympy-20154

The operation-by-operation correspondence between `Solution.lean`'s `gatherWalk`
impl region (plus the deep `stateAt` / `walkSeq` model) and `patch.diff` (the
gold patch). Each step is tagged **R** (type refinement), **A** (axiomatized
callee — **A-consumed** when the proof uses the axiom's `ensures`, **A-reference**
when a deep model is validated == the real callee by `axiom_check.py` / G-AX), or
**I** (identical concrete operation). The claim: *any implementation that
verifies against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** — it applies cleanly at `base_commit`
and is the real correctness oracle (G-RESOLVE).

## A. The change: per-yield duplication of the working record

Gold hunks (`sympy/utilities/iterables.py`, `partitions`):
```
- yield sum(ms.values()), ms          - yield ms
+ yield sum(ms.values()), ms.copy()   + yield ms.copy()
```
(twice each: the first yield at 1804-1807 and the loop yield at 1844-1847), plus
the deletion of the docstring caveat about the reused dictionary.

`Solution.lean` abstracts the GATHERING of the generator (`list(partitions(...))`
/ `[p for p in partitions(...)]` — exactly what the F2P tests do) into
`gatherWalk`, which records one value per step into `out : List Int`. The single
working dict the generator mutates in place is the live `work`; each yielded
object is a `snap` recorded into `out`.

| # | `Solution.lean` impl op (`gatherWalk`) | `patch.diff` op | tag | justification |
|---|---|---|---|---|
| A1 | the `while` loop recording one value per step into `out : List Int` | gathering the `partitions` generator (`list(...)` / list-comprehension over `for p in partitions(...)`) | R | gathering n yields ↔ a length-n list; the k-th yield ↔ `out[k]` (mapping.md §2). |
| A2 | `work := stateAt i` (advance the working state in place; the model carries the in-place advance as a backward enumeration) | the in-place mutation of `ms` through the generator's `while` loop body before each yield (`iterables.py:1809-1847`) | R | the working dict `ms` is mutated in place each step; its per-step CONTENT is abstracted to the strictly-increasing `stateAt i` (mapping.md §2). The F2P tests never depend on the dict's internal structure, only on whether gathered records are independent per-step snapshots. |
| A3 | `snap := stateAt (i-1); result := snap :: result` — record an INDEPENDENT per-step value before prepending | `yield ms.copy()` — yield a fresh independent copy of the working dict | A-reference | the changed operation is modeled **deeply**: the impl captures the working state BY VALUE (`snap := stateAt (i-1)`) so a later mutation of `work` never reaches an already-gathered record — precisely the independence `ms.copy()` provides. There is **no consumed copy axiom**; the proof never depends on one. The deep model's independence guarantee is validated **== the real `dict.copy()` / `partitions` semantics** out-of-band by `axiom_check.py` (G-AX): with `.copy()` the gathered list records the genuine pairwise-distinct per-step history; without it every gathered entry aliases the one dict and reads back as the final state (mapping.md §3.1). |
| A4 | `return result` (a `List Int`) | the gathered list the caller obtains | R | a list of the gathered records; the F2P tests compare these records element-by-element (mapping.md §2). |

The discriminating content of the change — each yielded record is an
INDEPENDENT snapshot of its step rather than a live alias of the one mutating
object — lives in `out[i]! = stateAt i` (model) ⇔ the `.copy()` at each `yield`
(real). The pre-image generator yields the live `ms`, so gathering collapses
every entry to the final state; `Solution_prepatch.lean` reproduces that (its
inner write-back loop re-aliases every gathered record to the current `work`)
and **fails** the postcondition `out[i]! = stateAt i` — exactly the spec sensing
the change (G-DIFF).

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — handing out an independent copy per yield instead of a live alias —
is modeled **deeply** (the by-value capture `snap := stateAt (i-1)` whose
independence is carried by the strictly-increasing per-step postcondition
`out[i]! = stateAt i`, step A3, an **A-reference**), not hidden behind an axiom
about the function under change. There is **no consumed axiom** in this bundle:
the only external semantics relied upon (`dict.copy()` independence) is the
A-reference that G-AX validates the deep model against; the proof itself is pure
structure/value logic (`List.range'` peeling).

## C. verify(model) ⇒ resolved

`gatherWalk` verifies only if every gathered record equals the snapshot of its
OWN step (A3), i.e. the gathered list recovers the strictly-increasing per-step
history rather than collapsing to a single final value. By R (gather ↔
`list(partitions(...))`; in-place `ms` mutation ↔ `work` advance; per-step dict
content ↔ `stateAt`) the verified gather equals `[p.copy() for p in
partitions(...)]` on the tested inputs; by G-AX the deep by-value independence
equals the real `ms.copy()` independence (A-reference), so the verified gather is
the gold patch up to type refinement and the audited duplication primitive — and
the gold patch resolves (G-RESOLVE). The single trust point is refinement
fidelity (this document, G-EQ); the A-reference duplication semantics are
additionally executable-checked (G-AX). There is no consumed-axiom trust point.
