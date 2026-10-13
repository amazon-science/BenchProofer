# refinement.md — pydata__xarray-3151

Operation-by-operation correspondence between `implementation_monotonicCheck`
(Solution.lean impl region) and `patch.diff` (the POST-PATCH monotonicity-check
loop inside `combine_by_coords`). Tags: **R** type refinement, **A-consumed**
proof uses an axiom, **A-reference** deep model validated == real callee, **I**
identical concrete op.

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `for d in dims do …` | `for dim in concat_dims:` (iterate the dimensions to validate) | R |
| 2 | `if d.variesBetweenInputs && !d.isMonotonic then return Except.error d.name` | `indexes = concatenated.indexes.get(dim); if not (indexes.is_monotonic_increasing or indexes.is_monotonic_decreasing): raise ValueError(... .format(dim))` | R |
| 3 | `return Except.ok ()` (loop completes) | loop completes; control continues to `concatenated_grouped_by_data_vars.append(concatenated)` | I |

## The R legs explained

- **Op 1 (carrier refinement).** The post-patch Python iterates `concat_dims` —
  exactly the dimensions that vary between the inputs and were concatenated along.
  The Lean impl iterates the FULL dimension list `dims` and applies the
  per-dimension guard `d.variesBetweenInputs`. These are order-preservingly
  equivalent: `concat_dims` is precisely the sublist `dims.filter
  (·.variesBetweenInputs)`, in the same order (mapping.md bijection). Iterating
  the filtered list and raising on the first non-monotonic member is the same
  observable behavior — same success/failure outcome and, on failure, the same
  first offending dimension name — as iterating the full list and raising on the
  first member that both varies and is non-monotonic. Modeling the full list lets
  the SAME carrier serve the pre-patch variant (which guards on `isCoordDim`
  instead), isolating the fix to the guard.
- **Op 2 (raise refinement).** `indexes.get(dim)` followed by the
  `is_monotonic_increasing or is_monotonic_decreasing` test is the upstream
  observation `d.isMonotonic` (true iff the global index is monotonic in either
  direction); its negation is the raise condition. The Python `raise
  ValueError(...format(dim))` ↔ the early `return Except.error d.name`; only the
  offending dimension name is behaviorally observed (mapping.md), so the message
  template is dropped. `indexes.get(dim)` is always defined for `dim in
  concat_dims` (every combined dimension carries an index), so the post-patch code
  needs no `if dim in concatenated` guard — the deleted guard's job is subsumed by
  iterating `concat_dims`.
- **Op 3 (fallthrough).** The loop completing without raising ↔ `Except.ok ()`:
  the object passes validation and is appended to the per-group results. Identical
  concrete control flow (I).

## Pre-patch correspondence (the bug)

The pre-patch Python loops over `concatenated.dims` guarded by `if dim in
concatenated` — i.e. it checks EVERY coordinate dimension, not only the combined
ones. `Solution_prepatch.lean` mirrors this exactly: the same scan over `dims`
with the guard `d.isCoordDim` (a coordinate dimension) instead of
`d.variesBetweenInputs`. The discriminating input is a non-monotonic **bystander**
coordinate (`isCoordDim = true`, `variesBetweenInputs = false`, `isMonotonic =
false`): the post-patch impl skips it and returns `Except.ok ()`, the pre-patch
impl raises `Except.error` on it — the exact issue in the F2P test
`test_combine_leaving_bystander_dimensions`. The carried gold proof body fails to
typecheck against the buggy impl (G-DIFF).

## Axioms / G-AX

**Every step is R or I — no A.** The behavior the patch changes (which dimensions
are subjected to the monotonicity requirement) is modeled DEEPLY and structurally
over the per-dimension observations; SPEC_GUIDE §3 forbids axiomatizing a
deeply-modeled changed decision. The `axioms` region is empty; **G-AX skips**.
The unchanged upstream callees (`is_monotonic_*` on the pandas index,
`_infer_concat_order_from_coords` producing `concat_dims`) are orthogonal to the
fix and enter as the grounded observations `isMonotonic` / `variesBetweenInputs`;
they leave no output component free — the spec pins the full result. **G-CONF**
mechanically refutes the R/I legs over ≥1e5 fuzzed inputs.
