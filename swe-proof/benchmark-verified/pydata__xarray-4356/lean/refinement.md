# refinement.md — pydata__xarray-4356

Operation-by-operation correspondence between `implementation_enforceMinCount`
(Solution.lean impl region) and `patch.diff` (the POST-PATCH `_maybe_null_out`
missing-value invalidation pass). Tags: **R** type refinement, **A-consumed**
proof uses an axiom, **A-reference** deep model validated == real callee, **I**
identical concrete op.

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | (no multi-axis guard; the `Id.run do` proceeds for any `axisSizes`) | the pre-patch `if hasattr(axis, "__len__"): raise ValueError(...)` is **deleted** by the patch — multi-axis reductions are no longer rejected | R |
| 2 | `let total : Int := (axisSizes.prod : Int)` | `np.take(mask.shape, axis).prod()` — product of the sizes of all reduced axes | R |
| 3 | `for cell in cells do out := out ++ [reducedCellValue total minCount fillValue cell]` | the element-wise construction of `null_mask` over the output cells and the application of `result[null_mask] = fill_value` | R |
| 3a | `reducedCellValue total minCount fillValue (v,missing) = if total - (missing:Int) < (minCount:Int) then fillValue else v` | `null_mask = (total - mask.sum(axis) - min_count) < 0`; where true, `result[cell] = fill_value`, else unchanged | R |
| 4 | `return .ok out` | `return result` (the invalidated array) | R |

Notes:

- **Grounded postcondition (directive 8).** `problem_spec_enforceMinCount` does
  NOT equate the result to a reference function sharing the impl's structure; it
  is an input-grounded relational predicate: `∃ out, result = .ok out ∧ ∀ i,
  out[i]? = (cells[i]?).map (fun cell => if axisSizes.prod − cell.2 < minCount
  then fillValue else cell.1)`. Quantifying over every index pins both the length
  and every element to the input carrier `cells` and the input `axisSizes` /
  `minCount` / `fillValue`, so only the genuine cell-wise product-count
  computation satisfies it (a wrong impl — e.g. one using a single-axis count, or
  filling the wrong cells — fails some index). `reducedCellValue` lives in the
  `pure` region as the impl's per-cell step only; it is not referenced by the
  spec.
- **Every step is R — no A, no I.** The op the patch changes (the per-cell total
  `np.take(mask.shape, axis).prod()` and the `< min_count` invalidation test) is
  modeled DEEPLY as `List.prod` + `Int` arithmetic; SPEC_GUIDE §3 forbids
  axiomatizing a deeply-modeled changed op. The `axioms` region is empty;
  **G-AX skips**.
- **R refinements.** `axis` (int or tuple/list) ↔ `axisSizes : List Nat` (the
  sizes `[mask.shape[a] for a in axis]`); `np.take(mask.shape, axis).prod()` ↔
  `axisSizes.prod`; `mask.sum(axis)` at a cell ↔ the supplied `missing : Nat`;
  the reduced `result` value at a cell ↔ `value : Float`; the numpy array result
  with fills applied ↔ `Except.ok (List Float)` (cell-wise). The signed test
  `(total - missing - min_count) < 0` is preserved by computing
  `total - (missing:Int) < (minCount:Int)` over `Int`, which is equivalent
  (`a - b - c < 0 ↔ a - b < c`).
- **The fix itself** is steps 1–2: pre-patch (`Solution_prepatch.lean`) keeps the
  multi-axis guard — `if axisSizes.length > 1 then return .error "..."` — which is
  the real `raise ValueError`, so `da.sum(["x","y"], min_count=...)` errors instead
  of being thresholded. That impl's carried gold proof fails to typecheck against
  the spec (the spec demands `.ok` for every input), giving G-DIFF its failing
  prepatch. The single-axis count change (`mask.shape[axis]` → product-of-one) is
  behavior-identical for one axis, so the discriminating observable is the
  multi-axis acceptance + product count — exactly what `test_min_count_nd`
  exercises (it reduces `["x","y","z"]` to a scalar).
- **Branch unification.** The real code has an nd-branch and a scalar `elif`
  branch computing the same logical decision (mapping.md): for an all-dims
  reduction `mask.size == ∏(reduced axis sizes)`, so the scalar branch's
  `mask.size - mask.sum() < min_count` test is the one-cell instance of the
  product rule. The Lean model captures the single decision over a list of cells
  (a 0-d result is the one-cell list), faithful to both branches.
- **Unmodeled (out of `min_count` scope).** The `axis is None` early path and the
  datetime-`NAT_TYPES` dtype guard are untouched by the patch and outside the
  reduction scenario the issue/F2P exercise (mapping.md "Modeled scope").
- **G-CONF** mechanically refutes the R legs: an in-process replica of the
  POST-PATCH decision (product count, no raise, positional fill marker) is diffed
  against the impl shadow over ≥1e5 fuzzed inputs crossing single- vs multi-axis
  reductions and per-cell missing counts spanning `0..total`. No A legs.
