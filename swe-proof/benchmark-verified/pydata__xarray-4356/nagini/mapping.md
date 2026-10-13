# mapping.md — pydata__xarray-4356

Model↔repo symbol binding, type abstraction, and callee provenance for the
twin-artifact bundle. All file:line references are at
`base_commit = e05fddea852d08fc0845f954b79deb9e9f9ff883`.

## 1. The modeled function

| model.py symbol | repo symbol | repo location (base_commit) |
|---|---|---|
| `flag_too_few(sizes, missing, required_minimum) -> bool` | the per-position `null_mask` element of `_maybe_null_out`'s multi-/single-axis reduction branch | `xarray/core/nanops.py:34-35` (function `_maybe_null_out`, lines 25-46) |

`_maybe_null_out` is invoked from `nansum` (`nanops.py:115`) and `nanprod`
(`nanops.py:185`) whenever `min_count is not None`. The branch the fix lives in
is `if axis is not None and getattr(result, "ndim", False):` (line 34), whose
body computes, for each output position,

```
null_mask = (mask.shape[axis] - mask.sum(axis) - min_count) < 0     # base_commit
null_mask = (np.take(mask.shape, axis).prod() - mask.sum(axis) - min_count) < 0   # fixed
```

`flag_too_few` models that boolean, element-wise, at one output position.

## 2. Type abstraction (the refinement carrier)

| repo reality | model.py carrier | bijection |
|---|---|---|
| `mask.shape` (a tuple of per-axis sizes) restricted to the reduced axes — i.e. `np.take(mask.shape, axis)` | `sizes: List[int]` (each > 0) | `sizes == [mask.shape[ax] for ax in axis]` = `np.take(mask.shape, axis)`. The model carries the **selected** reduced-axes sizes directly; the selection (`np.take`) is the refinement and is validated by axiom_check.py (A-reference). |
| `mask.sum(axis)` at one output position (count of `True`/missing entries reduced into that position) | `missing: int`, with `0 <= missing <= prod(sizes)` | identity on the per-position integer count. The bound `missing <= prod(sizes)` is exactly "at most the whole reduced block is missing". |
| `min_count` (the keyword argument, default 1) | `required_minimum: int` | identity. |
| `null_mask` element (a `bool`) | `Result(): bool` | identity. `null_mask.any()` over positions then governs the fill; the per-position truth value is what `flag_too_few` pins. |

The repo's `axis` (an `int` for a single dim, or a tuple/list for several) is
NOT a separate model parameter: what the computation needs from `axis` is only
the multiset of selected sizes `np.take(mask.shape, axis)`, which IS `sizes`.
`len(sizes) >= 1` models "at least one reduced axis" (the branch requires
`axis is not None`). A single reduced axis ⇒ `len(sizes) == 1` ⇒
`prod(sizes) == sizes[0]` (the fix coincides with the old single-axis code);
several reduced axes ⇒ `prod(sizes)` is the block size.

## 3. Deep-model reference (A-reference — validated by G-AX, NOT a consumed axiom)

The one changed quantity is the count of elements reduced over at a position:

- base_commit: `mask.shape[axis]` — the size of a **single** axis (and the
  function raises `ValueError` before reaching it whenever `axis` is a
  tuple/list, so multi-dim reductions with `min_count` were unavailable).
- fixed: `np.take(mask.shape, axis).prod()` — the **product** of the sizes
  along all reduced axes (the whole reduced block; coincides with `shape[axis]`
  for a single axis).

This composition `np.take(shape, axis).prod()` is modeled **deeply** in
model.py: `prod(ToSeq(sizes))` (the front-recursive product fold over the
selected sizes). There is no `@ContractOnly` axiom for it; instead the deep
model is validated **== the real callee** out-of-band:

| reference | real callee | provenance / flag dependency | checked_by |
|---|---|---|---|
| `prod(select(shape, axis))` (model.py `prod` over `sizes`) | `np.take(mask.shape, axis).prod()` | numpy `ndarray.prod` is the product over the array (empty product = 1); `numpy.take(a, indices)` gathers `a` at `indices`. The fix is integer-only (shape sizes are ints), precision-independent — no float encoding. Refs: numpy.org docs `numpy.take`, `numpy.ndarray.prod`; the gold patch `xarray/core/nanops.py` (this instance). | `axiom_check.py`: `prod(select(shape, axis)) == np.take(shape, axis).prod()` over 13 boundary + 4000 fuzz shape/axis cases, plus the full `null_mask` decision against the gold numpy expression on real boolean masks over 7 multi-axis array configurations. |

No flag dependency beyond numpy's defaults (`np.take` with no `axis`/`mode`
kwarg gathers from the flattened shape array; `prod` over the whole result).
There is no consumed axiom and therefore no opaque-callee soundness obligation.
