# refinement.md — django__django-13513

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`assembleReport` `do` block and the deep `flattenSeq` model) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement; state the
bijection), **A-consumed** (proof uses an axiom's `ensures`), **A-reference**
(deep model validated == real callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. There are **no A-tagged steps**
(no axioms, no deep-model callee references — see §C), so **G-AX = skip**.

Claim: any impl verifying against this frozen spec, refined per the map below,
is behaviorally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The frame-assembly change — `get_traceback_frames` (`django/views/debug.py:419–468`)

Gold hunk (assembly portion): the single `while tb is not None:` loop that
appended frames one exception at a time — advancing to the next exception only
when the current traceback was consumed (`if not tb.tb_next and exceptions:`) —
is replaced by:

```python
exc_value = exceptions.pop()
tb = self.tb if not exceptions else exc_value.__traceback__
frames.extend(self.get_exception_traceback_frames(exc_value, tb))
while exceptions:
    exc_value = exceptions.pop()
    frames.extend(
        self.get_exception_traceback_frames(exc_value, exc_value.__traceback__),
    )
return frames
```

i.e. `frames` becomes the in-order concatenation of **every** exception's frame
list, unconditionally — never halting because one exception's traceback was
empty.

| # | Solution.lean impl op (`assembleReport`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `groups : List (List Int)` | the chain of per-exception frame lists (each `get_exception_traceback_frames(e, e.__traceback__)`) | R | each exception's frame list ↔ one `List Int` element; the chain ↔ `List (List Int)`, in output order (mapping.md §2, §3.1). G-CONF bridges via frame-token ↔ `Int`. |
| A2 | `result := g ++ result` inside the backward `while` (folding each item's entries onto the front) | `frames.extend(self.get_exception_traceback_frames(...))` for each popped exception | I | `frames.extend(seq)` is list concatenation; the backward fold computes exactly the left-to-right concatenation `flattenSeq groups` (mapping.md §2). Concrete, transliterated by G-CONF. |
| A3 | result is `flattenSeq groups`: every item's entries, in order, an empty item skipped (not halting) | the post-patch report = `extend` over the full `exceptions` chain | A-reference? **No → I + R** | the changed assembly op is modeled **deeply** by `flattenSeq` (pure region); `flattenSeq` IS the concatenation, not a contract about an unchanged callee. The fold ops (`++`, the loop, `groups[i-1]!`) are **I**; the carrier abstraction is **R**. Its fidelity to the patched assembly is refuted by G-CONF, not G-AX. |
| A4 | `return result` (`List Int`) | `return frames` | R | identity on content; the F2P test observes `len(frames)` and frame membership, preserved by the token bijection (mapping.md §2). |

Discriminating content of the change — **an exception in the chain with an empty
frame list (empty traceback) must NOT terminate the assembly; every later
exception's frames still appear** — lives in `flattenSeq (g :: gs) = g ++
flattenSeq gs` with `flattenSeq [] = []` (an empty `g` contributes `[]` and the
recursion continues into `gs`). The pre-patch loop instead stops at the first
empty item; `Solution_prepatch.lean` reproduces that (it gathers only
`flattenSeq (groups.takeWhile (· ≠ []))`) and **fails** `out = flattenSeq groups`
(G-DIFF) — see §E.

## B. No `mut` frame leak

`groups` is **not** declared `mut` and is never rewritten — matching the real
loop, which only reads each per-exception frame list and concatenates it
(directive 5). `result` and `i` are the only mutated locals; the loop invariant
`result = flattenSeq (groups.drop i)` pins the accumulated value exactly, and
`done_with i = 0` plus `invariant i ≤ groups.length` pin termination — no
unconstrained `mut` state.

## C. No kind-3 (inexpressible-changed-op) steps; no axioms

Every step is R or I. The one operation that genuinely *changed* — assembling
the report from the per-exception frame lists without halting on an empty one —
is modeled **deeply** (`flattenSeq`, step A3), not hidden behind an axiom about
the function under change. The per-exception frame walk that PRODUCES each item
(`get_exception_traceback_frames`, a verbatim relocation of the unchanged inner
loop) is taken as the input carrier `groups`, so it is **neither axiomatized nor
deep-model-referenced** (mapping.md §3.1–3.2). Consequently there is **no
consumed axiom, no A-reference, and no `axiom_check.py`** (G-AX = skip).

## D. verify(Solution) ⇒ resolved

`assembleReport` verifies only if its output equals `flattenSeq groups` — every
item's entries, in order, with empty items skipped rather than halting (A3). By
R (frame-list ↔ `List Int`, chain ↔ `List (List Int)`, `extend` ↔ `++`,
`return frames` identity on content) the verified assembly equals the patched
`get_traceback_frames`'s `frames.extend(...)`-over-the-whole-chain behavior on
the tested inputs; by G-CONF the R/I transliteration of `flattenSeq` agrees with
`patch.diff`'s assembly behavior on ≥10⁵ fuzzed chains (including chains with
empty items in every position). Therefore a model satisfying this spec, refined
by the map above, is the gold patch up to type refinement — and the gold patch
resolves (G-RESOLVE). The single trust point is refinement fidelity (this doc,
G-EQ + G-CONF); there are no axioms to trust (G-AX vacuous).

## E. The prepatch fails on the right clause

`Solution_prepatch.lean` is byte-identical in spec (`ensures out = flattenSeq
groups`) and models the **pre-patch** assembly: it folds only over
`groups.takeWhile (· ≠ [])` — the items strictly before the first empty one,
because the real pre-patch loop ends as soon as an exception's traceback is
empty. Its `prove_correct` closes the loop-body goal (over the truncated prefix)
but leaves exactly one unsolved goal:

```
⊢ result_1 = flattenSeq groups
```

with hypothesis `result_1 = flattenSeq (groups.takeWhile (· ≠ []))`. These differ
whenever an early item is empty (e.g. `groups = [[], [1]]`:
`flattenSeq (takeWhile…) = []` but `flattenSeq groups = [1]`) — precisely the
F2P scenario `test_innermost_exception_without_traceback` (innermost exception
has no traceback ⇒ empty leading item ⇒ pre-patch drops the remaining frame).
The spec senses the bug (G-DIFF); no contract was weakened.
