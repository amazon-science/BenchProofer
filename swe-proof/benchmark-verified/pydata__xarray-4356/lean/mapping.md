# mapping.md — pydata__xarray-4356

## Symbol binding (file:line @ base_commit e05fddea852d08fc0845f954b79deb9e9f9ff883)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_enforceMinCount` / `problem_spec_enforceMinCount` | `_maybe_null_out(result, axis, mask, min_count)` (the missing-value invalidation pass) | `xarray/core/nanops.py:25-46` |
| `reducedCellValue` (pure helper) | the per-cell decision `(<total> - mask.sum(axis) - min_count) < 0 → fill_value` | `nanops.py:35-39` (nd branch) and `nanops.py:41-44` (scalar branch) |
| `Except.error msg` | `raise ValueError("min_count is not available for reduction with more than one dimensions.")` | `nanops.py:29-32` (pre-patch only; removed by the fix) |

## What the function does (base_commit)

```python
def _maybe_null_out(result, axis, mask, min_count=1):
    if hasattr(axis, "__len__"):  # if tuple or list
        raise ValueError(
            "min_count is not available for reduction with more than one dimensions."
        )
    if axis is not None and getattr(result, "ndim", False):
        null_mask = (mask.shape[axis] - mask.sum(axis) - min_count) < 0
        if null_mask.any():
            dtype, fill_value = dtypes.maybe_promote(result.dtype)
            result = result.astype(dtype)
            result[null_mask] = fill_value
    elif getattr(result, "dtype", None) not in dtypes.NAT_TYPES:
        null_mask = mask.size - mask.sum()
        if null_mask < min_count:
            result = np.nan
    return result
```

`_maybe_null_out` is the `min_count` post-processing applied after a `sum`/`prod`
reduction (`nansum`/`nanprod` call it when `min_count is not None`). `result` is
the already-reduced array; `mask` is the boolean null-mask of the *original*
(pre-reduction) array (`True` where the value was missing). For each output cell,
the number of elements reduced into it that were valid (non-missing) is

```
valid = (number of elements reduced into the cell) - (number of missing ones)
```

and the cell is *invalidated* (overwritten with the promoted fill value, NaN for
floats) when `valid < min_count`, i.e. when `total - missing - min_count < 0`.

**The bug.** Pre-patch, any tuple/list `axis` (a reduction over more than one
dimension) hits the `hasattr(axis, "__len__")` guard and raises `ValueError`, so
`da.sum(["x", "y"], min_count=1)` fails outright. Additionally, even if that
guard were lifted, `mask.shape[axis]` cannot index a shape tuple with a list, and
for a single axis it only yields the size of *that one* axis.

**The fix.** Remove the guard and compute the per-cell total number of reduced
elements as `np.take(mask.shape, axis).prod()` — the product of the sizes of all
reduced axes. For a single `int` axis this product equals the old
`mask.shape[axis]` (a product of one factor), so single-axis behavior is
unchanged; for a multi-axis reduction it is the true count of elements reduced
into each cell. The two changes are coupled: the guard cannot be removed without
also generalising the index to a product, because a shape tuple cannot be indexed
by a list.

**Branch unification (faithfulness note).** The nd branch (`result.ndim` truthy:
some but not all dims reduced) and the scalar `elif` branch (all dims reduced →
0-d result) compute the *same* logical decision. In the scalar branch
`total = mask.size = ∏(all dims)` and, since all axes are reduced there,
`mask.size = ∏(mask.shape[a] for a in axis)` = the same product the nd branch
uses. Both invalidate a cell iff `valid < min_count`. The Lean model captures the
single logical decision over a list of output cells; a 0-d (all-dims-reduced)
result is the one-cell list. This is exactly the F2P scenario
(`test_min_count_nd` reduces `["x","y","z"]` → scalar): pre-patch it raised;
post-patch the product-based count produces a value.

## Lean modeling

- The function reads `mask` and `result` (numpy arrays) and `axis` (an int or a
  list of ints). The observables that determine the output are abstracted to
  faithful inputs:
  - `axisSizes : List Nat` = `[mask.shape[a] for a in axis]`, the sizes of the
    reduced axes. `hasattr(axis, "__len__")` (multi-dim reduction) ⟺
    `axisSizes.length > 1`; a single `int` axis ⟺ `axisSizes.length = 1`.
    `np.take(mask.shape, axis).prod()` = `axisSizes.prod`.
  - `cells : List (Float × Nat)` = one entry per output cell, `(value, missing)`,
    where `value` is the reduced `result` value at that cell and `missing` =
    `mask.sum(axis)` at that cell (a pure, deterministic function of `mask`, taken
    as input). A 0-d result is a one-element list.
  - `minCount : Nat` = `min_count`.
  - `fillValue : Float` = the promoted fill value from `dtypes.maybe_promote`
    (NaN for float dtypes), taken as an input observable.
- Output: the array after invalidation, modeled as `Except String (List Float)` —
  `.error msg` for the pre-patch `raise`, `.ok out` for the normal return where
  `out[i] = fillValue` when cell `i` is invalidated, else the unchanged
  `result[i]`. The post-patch function never raises (for the modeled numeric,
  axis-given case), so the spec pins `result = .ok (...)`.
- The per-cell decision `reducedCellValue total minCount fillValue (v, missing)`
  = `if total - missing < minCount then fillValue else v`, with
  `total = (axisSizes.prod : Int)`. The signed comparison `< 0` of the original
  (`total - missing - min_count < 0`) is preserved by computing over `Int`.

### Modeled scope / preconditions
The model covers the case `min_count` actually addresses: `axis` given (a
non-empty set of reduced axes) over a numeric result. The unchanged `axis is
None` early-return and the datetime-`NAT_TYPES` dtype guard are dtype/None edge
conditions the patch does not touch and are outside the `min_count` reduction
scenario the issue and F2P tests exercise; they are not modeled.

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | bijection |
|---|---|---|
| `axis` int | `axisSizes : List Nat`, length 1 | the one reduced-axis size |
| `axis` tuple/list | `axisSizes : List Nat`, length > 1 | the reduced-axis sizes, in order |
| `np.take(mask.shape, axis).prod()` | `axisSizes.prod` | product of the factors (`Nat`→`Int` cast) |
| `mask.sum(axis)` at a cell | `cell.2 : Nat` | non-negative missing-element count |
| `result` value at a cell | `cell.1 : Float` | identity (payload) |
| `min_count` | `minCount : Nat` | identity |
| `dtypes.maybe_promote(...)` fill | `fillValue : Float` | the promoted fill (NaN for floats) |
| `(total - missing - min_count) < 0` | `total - (missing:Int) < (minCount:Int)` | `< 0` ⟺ `valid < min_count` |
| `raise ValueError(msg)` | `Except.error msg` | pre-patch multi-dim guard |
| normal return (array w/ fills) | `Except.ok out` | `out` = cell-wise invalidated values |

## Callee provenance + flag dependencies

- **No consumed callee axiom; no A-reference.** The op the patch changes — the
  per-cell count `np.take(mask.shape, axis).prod() - mask.sum(axis)` and its
  comparison to `min_count` — is modeled DEEPLY (`axisSizes.prod`, `Int`
  arithmetic, the `if`). SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled
  changed op, so the `axioms` region is empty and **G-AX skips**.
- `mask.sum(axis)` and `dtypes.maybe_promote` are unchanged; their *results*
  (`cell.2`, `fillValue`) are taken as input observables, not recomputed, so no
  callee contract is needed. `mask.sum(axis)` is a deterministic function of the
  (input) mask; `maybe_promote` only chooses the fill sentinel, which the F2P
  tests observe only positionally (`assert_allclose`).
- Flag dependency: `nansum`/`nanprod` call `_maybe_null_out` only when
  `min_count is not None`; the modeled inputs assume that call site.

## G-CONF fuzz seed

Pinned LCG seed: **4356** (see `conformance_check.py` `SEED`). The R/I shadow of
`implementation_enforceMinCount` (the product-based per-cell decision) is diffed
against an in-process replica of the POST-PATCH `_maybe_null_out` decision
(`(np.take(shape, axis).prod() - missing - min_count) < 0`, with the fill applied
positionally) over ≥1e5 fuzzed inputs crossing single- vs multi-axis reductions,
varied `min_count`, and per-cell missing counts spanning `0..total`. Edge cases
pin the F2P scenario: a multi-axis reduction (`axisSizes` of length ≥ 2) where the
single-axis (buggy) count would invalidate different cells than the product count.
