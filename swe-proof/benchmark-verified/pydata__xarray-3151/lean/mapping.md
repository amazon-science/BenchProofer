# mapping.md — pydata__xarray-3151

## Symbol binding (file:line @ base_commit 118f4d996e7711c9aced916e6049af9f28d5ec66)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_monotonicCheck` / `problem_spec_monotonicCheck` | the post-concatenation monotonicity-validation loop inside `combine_by_coords` | `xarray/core/combine.py:503-511` |
| `Dim` (pure helper) | one dimension of the just-concatenated object together with the three observations the loop reads about it | the loop variable `dim` + `dim in concatenated` + `concat_dims` membership + `indexes.is_monotonic_*` |
| `firstNonMonotonicVarying` (pure helper) | the loop body: raise `ValueError` for the first checked dimension whose global index is neither monotonically increasing nor decreasing | `combine.py:503-511` |

The modeled behavior is the **per-group monotonicity validation** that runs after
the multidimensional combine. It is the only behavior the patch changes and the
only behavior the FAIL_TO_PASS test (`test_combine_leaving_bystander_dimensions`)
observes.

### What the code does (base_commit)

For each group of datasets sharing the same data variables, `combine_by_coords`
infers an ordering, concatenates along the dimensions that **vary between the
inputs** (`concat_dims`, returned by `_infer_concat_order_from_coords`), and then
validates the result:

```python
# base_commit (buggy):
for dim in concatenated.dims:          # ALL dimensions of the result
    if dim in concatenated:            # ... that are also coordinate dimensions
        indexes = concatenated.indexes.get(dim)
        if not (indexes.is_monotonic_increasing
                or indexes.is_monotonic_decreasing):
            raise ValueError("Resulting object does not have monotonic"
                             " global indexes along dimension {}".format(dim))
```

`concatenated.dims` are every dimension of the combined object; `dim in
concatenated` is true exactly for the dimensions that carry a coordinate index.
So the loop checks **every coordinate dimension** for monotonicity — including a
*bystander* coordinate (one that is identical across all input datasets and was
therefore never concatenated along). A non-monotonic bystander coordinate (e.g.
`y = ['a','c','b']`, shared by every input) wrongly trips the `ValueError`, even
though the documentation promises such "coordinate dimensions which do not vary
between each dataset" are ignored.

The fix restricts the loop to `concat_dims` — the dimensions actually
concatenated along (the ones that vary between inputs):

```python
# post-patch (fixed):
for dim in concat_dims:
    indexes = concatenated.indexes.get(dim)
    if not (indexes.is_monotonic_increasing
            or indexes.is_monotonic_decreasing):
        raise ValueError(... dim ...)
```

Every `dim in concat_dims` necessarily carries an index, so the inner
`if dim in concatenated` guard is no longer needed.

### Lean modeling

The two versions iterate the **same** collection of dimensions and differ only in
the per-dimension guard deciding whether that dimension is checked:

- pre-patch guard: *is this a coordinate dimension?* (`dim in concatenated`)
- post-patch guard: *does this dimension vary between the inputs?*
  (`dim in concat_dims`)

So I model the loop's carrier as the list of all the combined object's
dimensions, each tagged with the three observations the loop reads, and capture
the patch as the change of guard over that common carrier:

```lean
structure Dim where
  name        : String   -- the dimension name (carried into the error message)
  isCoordDim  : Bool     -- the dimension carries a coordinate index (`dim in concatenated`)
  variesBetweenInputs : Bool  -- the dimension was combined across the inputs (`dim in concat_dims`)
  isMonotonic : Bool     -- its global index is monotonic increasing OR decreasing
```

- **Result.** The loop either completes (success — the object passes the check)
  or raises `ValueError` naming the first offending dimension. Modeled as
  `Except String Unit`: `.ok ()` on success, `.error name` on the raise.
- **Post-patch (Solution).** `firstNonMonotonicVarying` / `implementation_monotonicCheck`
  scans the dims in order and raises on the first one with
  `variesBetweenInputs ∧ ¬isMonotonic`. Scanning the full list while guarding on
  `variesBetweenInputs` is order-preservingly equivalent to iterating
  `concat_dims` directly (`concat_dims` is the `variesBetweenInputs` sublist, in
  the same order) — the R refinement recorded in refinement.md.
- **Pre-patch.** Same scan, guard `isCoordDim ∧ ¬isMonotonic`. This raises on a
  non-monotonic bystander coordinate (`isCoordDim ∧ ¬variesBetweenInputs ∧
  ¬isMonotonic`), reproducing the bug.

The error message text and the `.format(dim)` are not behaviorally observed by
the F2P test beyond which dimension (if any) triggers the raise, so the model
carries only the dimension `name`.

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | bijection |
|---|---|---|
| a dimension of the combined object | `Dim` | record of the four observations below |
| the dimension name (a hashable label) | `name : String` | any total injection of labels to strings; G-CONF uses the labels verbatim |
| `dim in concatenated` (carries an index) | `isCoordDim : Bool` | identity |
| `dim in concat_dims` (varies between inputs) | `variesBetweenInputs : Bool` | identity |
| `indexes.is_monotonic_increasing or indexes.is_monotonic_decreasing` | `isMonotonic : Bool` | identity |
| loop completes without raising | `Except.ok ()` | identity |
| `raise ValueError(... dimension {dim})` | `Except.error name` | the raised dimension ↔ `name` |
| `concatenated.dims` (the iteration carrier) | `dims : List Dim` | order-preserving list of the object's dimensions |

`concat_dims` (the post-patch carrier) ↔ `dims.filter (·.variesBetweenInputs)`,
in order. Every `concat_dim` carries an index, hence
`variesBetweenInputs → isCoordDim` for the real inputs (an invariant, not a spec
precondition — the spec holds for all `Dim` lists).

## Callee provenance + flag dependencies

- **No consumed callee axiom and no A-reference.** `is_monotonic_increasing` /
  `is_monotonic_decreasing` are pandas index properties, and `_infer_concat_order_from_coords`
  (which produces `concat_dims`) are UNCHANGED by the patch; their results enter
  the model as the grounded per-dimension observations `isMonotonic` and
  `variesBetweenInputs`. The behavior the patch changes — *which* dimensions are
  subjected to the monotonicity check — is modeled DEEPLY and structurally over
  those observations (SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled changed
  decision). So the `axioms` region is empty and **G-AX skips**. The R legs are
  validated by G-CONF.
- The monotonicity of a dimension's global index depends only on the concatenated
  coordinate values; `variesBetweenInputs` is determined upstream by
  `_infer_concat_order_from_coords` (a dimension varies, and is concatenated
  along, iff its coordinate values differ between the input datasets). Both are
  orthogonal to the fix and carried as observations.

## G-CONF fuzz seed

Pinned LCG seed: **3151** (see `conformance_check.py` `SEED`). Corpus: randomized
`List Dim` of varied length, crossing every combination of the three flags, with
emphasis on the discriminating category — a non-monotonic **bystander** coordinate
(`isCoordDim=True`, `variesBetweenInputs=False`, `isMonotonic=False`) that the
post-patch loop must ignore but the pre-patch loop raised on — plus controls with
non-monotonic *varying* dimensions (must still raise on the first such, in order)
and all-monotonic inputs (must succeed). The R/I shadow of
`implementation_monotonicCheck` is diffed against an in-process replica of the
POST-PATCH loop over ≥1e5 fuzzed inputs.
