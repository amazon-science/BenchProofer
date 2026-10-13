# refinement.md — matplotlib__matplotlib-22865

The operation-by-operation correspondence between `model.py`'s implementation
(the `drawn_separators` impl region, with the deep `start_index` / `end_index`
helpers) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — **A-consumed** where the proof uses an
axiom's `Ensures`; **A-reference** where a deep model is validated == the real
callee/operation by axiom_check.py / G-AX), or **I** (identical concrete
operation). The claim: *any implementation that verifies against this frozen
spec, refined per the map below, is behaviourally equal to the gold patch on
the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The divider-segment selection — `Colorbar._add_solids` (`lib/matplotlib/colorbar.py:634`)

Gold hunk (body lines 654-655 → the new conditional):
```
- self.dividers.set_segments(
-     np.dstack([X, Y])[1:-1] if self.drawedges else [])
+ if self.drawedges:
+     start_idx = 0 if self._extend_lower() else 1
+     end_idx = len(X) if self._extend_upper() else -1
+     self.dividers.set_segments(np.dstack([X, Y])[start_idx:end_idx])
+ else:
+     self.dividers.set_segments([])
```

| # | model.py impl op (`drawn_separators`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `segments: List[int]` | `np.dstack([X, Y])` (an `(n,2,2)` array) | R | each candidate segment is identified by its mesh-row position; `List[int]` of position ids ↔ first-axis of the array (mapping.md §2). |
| A2 | param `lower_open: bool` | `self._extend_lower()` | R/I | identical boolean; the predicate is UNCHANGED by the patch (mapping.md §3.1), supplied as an input. |
| A3 | param `upper_open: bool` | `self._extend_upper()` | R/I | identical boolean; unchanged predicate, supplied as an input. |
| A4 | `start = 0 if lower_open else 1` (== `start_index(lower_open)`) | `start_idx = 0 if self._extend_lower() else 1` | I | identical concrete conditional on the boolean. |
| A5 | `end = len(segments) if upper_open else len(segments) - 1` (== `end_index(upper_open, n)`) | `end_idx = len(X) if self._extend_upper() else -1` | A-reference | `len(X) == len(segments) == n` (R). The real `-1` upper bound and the model's `n-1` are identical under Python/numpy basic first-axis slicing on a length-`n` array (both drop exactly the last element); G-AX asserts the resulting kept run is identical (mapping.md §3.1). |
| A6 | the copy loop materialising `segments[start:end]` | `np.dstack([X, Y])[start_idx:end_idx]` | A-reference | basic first-axis slicing ↔ the verified copy loop over `[start, end)`; element-wise equality pinned by the result postcondition. G-AX validates the deep model == the real slice on canonical + exhaustive-small + fuzz configs. |
| A7 | `Result()` returned (a `List[int]`) | `self.dividers.set_segments(...)` | R | `set_segments` stores its argument; the F2P assertion reads it back via `get_segments()`. Modeled as the identity on the segment sequence (mapping.md §2). |

The discriminating content of the change — that the kept run's bounds depend on
the two open-ended-limit booleans rather than being the fixed `[1:-1]` — lives
in `start_index` / `end_index` (model) ⇔ the `start_idx` / `end_idx`
computation (real). The pre-patch slice was the unconditional `[1:-1]`;
`model_prepatch.py` reproduces that (`start=1, end=n-1` regardless of the
booleans) and **fails** the postcondition
`len(Result()) == end_index(upper_open, len(segments)) - start_index(lower_open)`,
which is exactly the spec sensing the change (G-DIFF): for `extend='both'`
both booleans are true, the spec demands the full run of length `n`, and the
prepatch produces length `n-2`.

## B. No consumed axiom

There is no `@ContractOnly` axiom the proof consumes. The only callees involved
in the kept-run selection are (i) the two boolean predicates `_extend_lower` /
`_extend_upper`, which are UNCHANGED and enter the model as plain boolean
inputs (R/I, rows A2-A3), and (ii) basic array slicing, which is modeled DEEPLY
by the verified copy loop and validated as an **A-reference** (rows A5-A6) by
`axiom_check.py` (G-AX). Shipping a dead `@ContractOnly` here would be a hygiene
defect; none is shipped.

## C. The `drawedges=False` branch is identical pre/post-patch

Both pre- and post-patch set `self.dividers.set_segments([])` when
`drawedges` is false; that branch is unchanged (tag **I**), and every F2P /
relevant P2P test that exercises the changed behaviour uses `drawedges=True`.
The model therefore models only the `drawedges=True` branch (the changed one);
the unchanged empty branch needs no differential witness.

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the slice-bound selection — is modeled **deeply** (the spelled-out
`start_index` / `end_index` helpers consumed in `drawn_separators`, rows A4-A6,
**A-reference**), not hidden behind an axiom about the function under change.

## E. verify(model) ⇒ resolved

`drawn_separators` verifies only if its output is exactly
`segments[start_index(lower_open) : end_index(upper_open, n)]` (length
clause A5 + element-wise clause A6) — i.e. the boolean-driven kept run, with the
full run kept when both limits are open ended. By R (`np.dstack` first-axis ↔
`List[int]` of position ids; `len(X)`↔`len(segments)`; `set_segments`/`get_segments`
identity on content) the verified selection equals
`np.dstack([X, Y])[start_idx:end_idx]` on the tested inputs; by G-AX the deep
model `start_index`/`end_index` + slice loop equals the real selection
(A-reference) under the unchanged `_extend_lower`/`_extend_upper` predicates.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the audited A-reference — and the gold patch
resolves (G-RESOLVE). The trust points are exactly those of PLAN §1.1: the
A-reference soundness (G-AX) and refinement fidelity (this document, G-EQ);
there is no consumed-axiom trust point.
