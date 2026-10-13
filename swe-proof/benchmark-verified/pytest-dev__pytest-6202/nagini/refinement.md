# refinement.md — pytest-dev__pytest-6202

The operation-by-operation correspondence between `model.py`'s implementation
(the `modpath_of` impl region and the deep `join_dot` model) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement), **A** (a callee —
**A-consumed** where the proof uses an axiom's `Ensures`, **A-reference** where a
deep model is validated == the real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The modeled change — `getmodpath()` (`src/_pytest/python.py:271`)

Gold hunk (the only change to the function body):
```
-        s = ".".join(parts)
-        return s.replace(".[", "[")
+        return ".".join(parts)
```

The lines above the hunk (the `listchain` walk that builds `parts`, lines
273-287) are UNCHANGED and upstream of the edit. The modeled function
`modpath_of(parts)` takes the resulting `parts` as input and models the tail
that the patch edits.

| # | model.py impl op (`modpath_of`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `parts: PSeq[PSeq[int]]` | `parts: List[str]` (the accumulated name parts) | R | `str` ↔ `PSeq[int]` code points; `List[str]` ↔ `PSeq[PSeq[int]]` (mapping.md §2). The `parts`-building prefix of `getmodpath` is unchanged and produces this list in both pre- and post-patch code. |
| A2 | `Requires(len(parts) >= 1)` | (no node) | I | `getmodpath` always appends at least the node's own `name` to `parts` (`python.py:286`), so `parts` is non-empty at the join — a faithful precondition, not a spec weakening. |
| A2b | `Requires(MustTerminate(2))` | (no node) | I | the real `getmodpath` always RETURNS its path (a single finite `".".join` over a finite list); termination is part of the specified behaviour. Nagini is partial-correctness by default, so without the obligation a diverging implementation satisfies `Ensures(Result() == join_dot(parts))` vacuously (the audit's P1 `atk_9_nonterm_reachable.py` exploited exactly this). The obligation pins total correctness: any loop must carry a strictly decreasing, bounded-below `MustTerminate` measure. It is faithful (not too strong): the gold code is a single terminating pass, and the verified backward fold discharges the obligation with measure `i + 1`. |
| A3 | result is `join_dot(parts)`, the dot-join computed by the backward fold over `parts` | `".".join(parts)` | A-reference | the join is modeled **deeply**: `join_dot` (the spelled-out front-recursive fold in the `pure` region) and the verified backward loop in `modpath_of` ARE the dot-join. There is no consumed `join` axiom — the proof never depends on one. The deep model is validated **== the real callee** out-of-band: G-AX (axiom_check.py) runs `".".join(...)` on boundary+fuzz and asserts `".".join == join_dot`. (mapping.md §3.1.) |
| A4 | `return result` (no further transformation) | `return ".".join(parts)` (no further transformation) | I | the gold returns the join directly; `modpath_of` returns `result == join_dot(parts)` directly. The absence of any post-join substitution IS the fix, and it is pinned by the postcondition `Result() == join_dot(parts)`. |

The discriminating content of the change — that **no** `.replace(".[", "[")`
post-join substitution is applied — lives in the postcondition
`Result() == join_dot(parts)` (an exact structural equality grounded in the
input carrier `parts`, not an oracle; SPEC_GUIDE directive 8). The pre-patch code
applied that substitution; `model_prepatch.py` reproduces it (the second impl
loop computing `replace_db(join_dot(parts))`) and **fails** the postcondition,
which is exactly the spec sensing the change (G-DIFF; verified failure on
`Result() == join_dot(parts)`).

## B. The pre-patch substitution — `replace_db` (prepatch witness only)

| # | model_prepatch.py construct | pre-patch repo op | tag | justification |
|---|---|---|---|---|
| B1 | the second impl loop building `result` = `s.replace(".[","[")` of the join | `s.replace(".[", "[")` (`python.py:289`, removed by the fix) | A-reference | the removed substitution is the **changed** operation, so it is NOT an axiom; it is modeled deeply (left-to-right non-overlapping replacement of `[46,91]` by `[91]`) only inside the prepatch impl to witness the bug. G-AX validates `replace_db == str.replace`. It is *not* part of the shared spec view (it lives entirely in the elided impl region), so `same_spec(model, prepatch)` holds (G-DIFF). |

Because the two characters of the pattern `".["` are distinct, CPython's
non-overlapping left-to-right `str.replace` coincides with the greedy scan
`replace_db` encodes (mapping.md §3.2); axiom_check.py confirms this on boundary
+ 30000 fuzz inputs.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The two operations the patch touches —
the `str.join` (kept) and the `str.replace` (removed) — are both modeled
**deeply** over `PSeq[int]` (the front-recursive folds `join_dot` and the
prepatch's `replace_db`), not hidden behind any consumed axiom. There is **no
`@ContractOnly` axiom in this bundle.** Both deep models are validated == their
real CPython callees by G-AX (axiom_check.py).

## D. verify(model) ⇒ resolved

`modpath_of` verifies only if it TERMINATES (A2b: the `MustTerminate(2)`
obligation — a diverging implementation is rejected, closing the
partial-correctness admission the audit found) and its output equals the exact
dot-join of the parts with NO further substitution (A3 + A4), pinned by
`Result() == join_dot(parts)`.
By R (`str` ↔ `PSeq[int]`, `List[str]` ↔ `PSeq[PSeq[int]]`) the verified result
equals `".".join(parts)` on the tested inputs; by G-AX the deep model `join_dot`
equals the real `str.join` (A-reference). The gold patch returns exactly
`".".join(parts)` with no substitution, so a model satisfying this spec, refined
by the map above, IS the gold patch up to type refinement — and the gold patch
resolves (G-RESOLVE). The F2P test observes `getmodpath() ==
"TestY.testmethod_two[.[]"` for a parametrised test whose part name contains
`.[`; the gold (plain join) produces it, the pre-patch (join + substitution)
corrupts it to `TestY.testmethod_two[[]` — exactly the discrimination the spec
encodes. The single trust point of PLAN §1.1 active here is axiom/deep-model
soundness (G-AX); refinement fidelity is this document (G-EQ). No consumed axiom
trust point exists (there is no `@ContractOnly`).
