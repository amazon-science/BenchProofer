# refinement.md — pytest-dev__pytest-6202

The operation-by-operation correspondence between `Solution.lean`'s
implementation (the `joinPath` impl region and the deep `joinDot` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (the proof uses an axiom's `ensures`), **A-reference** (a deep
model validated == the real callee by axiom_check.py / G-AX), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold patch
on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The modeled change — `getmodpath()` (`src/_pytest/python.py:271`)

Gold hunk (the only change to the function body):
```
-        s = ".".join(parts)
-        return s.replace(".[", "[")
+        return ".".join(parts)
```

The lines above the hunk (the `listchain` walk that builds `parts`, then
`parts.reverse()`, lines 273–287) are UNCHANGED and upstream of the edit. The
modeled function `joinPath(parts)` takes the resulting `parts` as input and
models the tail that the patch edits.

| # | Solution.lean impl op (`joinPath`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `parts : List (List Char)` | `parts: List[str]` (the accumulated, reversed name parts) | R | `str` ↔ `List Char`; `List[str]` ↔ `List (List Char)` (mapping.md §2). The `parts`-building prefix of `getmodpath` is unchanged and produces this list in both pre- and post-patch code. |
| A2 | `require parts.length ≥ 1` | (no node) | I | `getmodpath` always appends at least the node's own `name` to `parts` (`python.py:286`), so `parts` is non-empty at the join — a faithful precondition, not a spec weakening. |
| A3 | result is `joinDot parts`, the separator-join computed by the backward fold over `parts` | `".".join(parts)` | A-reference | the join is modeled **deeply**: `joinDot` (the front-recursive fold in the `pure` region) and the verified backward loop in `joinPath` ARE the dot-join. There is no consumed `join` axiom — the proof never depends on one. The deep model is validated **== the real callee** out-of-band: G-AX (axiom_check.py) runs `".".join(...)` on boundary+fuzz and asserts `".".join == joinDot`. (mapping.md §3.1.) |
| A4 | `return result` (no further transformation) | `return ".".join(parts)` (no further transformation) | I | the gold returns the join directly; `joinPath` returns `result == joinDot parts` directly. The absence of any post-join substitution IS the change, and it is pinned by the postcondition `out = joinDot parts`. |

The discriminating content of the change — that **no** `.replace(".[", "[")`
post-join substitution is applied — lives in the postcondition
`out = joinDot parts` (an exact structural equality grounded in the input
carrier `parts`, not an oracle; SPEC_GUIDE directive 8).

**Termination semantics.** The bundle uses TOTAL correctness
(`loom.semantics.termination "total"`, `open TotalCorrectness`): the real
join over the accumulated name parts is a bounded loop and always terminates,
so a diverging implementation (e.g. an infinite `while` that never reaches the
postcondition) must NOT satisfy the spec. Under partial correctness such an
implementation would discharge the postcondition vacuously — a spec-too-weak
hole. The verified loop carries `decreasing i` to discharge the totality
obligation. The pre-patch code
applied that substitution; `Solution_prepatch.lean` reproduces it (the impl
applies `replaceWindow` to the join) and **fails** the postcondition, which is
exactly the spec sensing the change (G-DIFF; verified failure on the
`ensures out = joinDot parts` clause — the unsolved goal is
`replaceWindow result = joinDot parts`).

## B. The pre-patch substitution — `replaceWindow` (prepatch witness only)

| # | `Solution_prepatch.lean` construct | pre-patch repo op | tag | justification |
|---|---|---|---|---|
| B1 | the impl applies `replaceWindow` to the join `result` | `s.replace(".[", "[")` (`python.py:289`, removed by the fix) | A-reference | the removed substitution is the **changed** operation, so it is NOT an axiom; it is modeled deeply (left-to-right non-overlapping replacement of `['.','[']` by `'['`) only inside the prepatch impl to witness the bug. G-AX validates `replaceWindow == str.replace`. `replaceWindow` is a spec-neutral helper present in BOTH `pure` regions (so `same_spec` holds, G-DIFF) but referenced ONLY by the prepatch impl. |

Because the two characters of the pattern `".["` are distinct, CPython's
non-overlapping left-to-right `str.replace` coincides with the greedy scan
`replaceWindow` encodes (mapping.md §3.2); axiom_check.py confirms this on
boundary + fuzz inputs.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The two operations the patch touches —
the `str.join` (kept) and the `str.replace` (removed) — are both modeled
**deeply** over `List Char` (the front-recursive folds `joinDot` and the
prepatch-referenced `replaceWindow`), not hidden behind any consumed axiom.
There is **no consumed `axiom` in this bundle.** Both deep models are validated
== their real CPython callees by G-AX (axiom_check.py).

## D. verify(model) ⇒ resolved

`joinPath` verifies only if its output equals the exact separator-join of the
parts with NO further substitution (A3 + A4), pinned by `out = joinDot parts`.
By R (`str` ↔ `List Char`, `List[str]` ↔ `List (List Char)`) the verified result
equals `".".join(parts)` on the tested inputs; by G-AX the deep model `joinDot`
equals the real `str.join` (A-reference). The gold patch returns exactly
`".".join(parts)` with no substitution, so a model satisfying this spec, refined
by the map above, IS the gold patch up to type refinement — and the gold patch
resolves (G-RESOLVE). The F2P test observes `getmodpath() ==
"TestY.testmethod_two[.[]"` for a parametrised test whose part name contains
`.[`; the gold (plain join) produces it, the pre-patch (join + substitution)
corrupts it to `TestY.testmethod_two[[]` — exactly the discrimination the spec
encodes. The single trust point of PLAN §1.1 active here is axiom/deep-model
soundness (G-AX); refinement fidelity is this document (G-EQ). No consumed-axiom
trust point exists.
