# refinement.md — pydata__xarray-4356

Operation-by-operation correspondence between `model.py`'s implementation (the
`flag_too_few` impl region and the deep `prod` model) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement — same operation, refined
carrier type), **A-consumed** (proof uses a `@ContractOnly` axiom's `Ensures`),
**A-reference** (a deep model is validated == the real callee by axiom_check.py
/ G-AX, NOT consumed), or **I** (identical concrete operation). The claim: *any
implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## Gold hunk (`xarray/core/nanops.py`, function `_maybe_null_out`)

```
-    if hasattr(axis, "__len__"):  # if tuple or list
-        raise ValueError(
-            "min_count is not available for reduction with more than one dimensions."
-        )

     if axis is not None and getattr(result, "ndim", False):
-        null_mask = (mask.shape[axis] - mask.sum(axis) - min_count) < 0
+        null_mask = (np.take(mask.shape, axis).prod() - mask.sum(axis) - min_count) < 0
```

The fix has two coupled parts: (a) delete the early `raise ValueError` that
forbade a tuple/list `axis`, and (b) replace the single-axis element count
`mask.shape[axis]` with the whole-block count `np.take(mask.shape, axis).prod()`.
Both are the SAME behavioural change — "count the whole reduced block, allowing
many reduced axes" — observed at the one expression `flag_too_few` models.

| # | model.py impl op (`flag_too_few`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | parameter `sizes: List[int]` (the reduced-axes sizes) | the value `np.take(mask.shape, axis)` | R | `np.take(mask.shape, axis)` ↔ `[mask.shape[ax] for ax in axis]` = `sizes` (mapping.md §2). `len(sizes) >= 1` ↔ "at least one reduced axis" (the branch's `axis is not None`); `len(sizes) >= 2` is exactly the multi-dim case the old `raise` forbade. |
| 2 | parameter `missing: int` | `mask.sum(axis)` at one output position | R | identity on the per-position integer count of missing (`True`) entries; the postcondition is element-wise, matching numpy's element-wise `(... ) < 0` (mapping.md §2). |
| 3 | parameter `required_minimum: int` | `min_count` | I | identity (the keyword argument). |
| 4 | `total = 1; for k: total = total * sizes[k]` — i.e. `total == prod(ToSeq(sizes))` | `np.take(mask.shape, axis).prod()` | A-reference | the changed quantity is modeled **deeply**: `prod` (the front-recursive product fold in the `pure` region) over the selected sizes IS the take-then-product. There is no consumed `@ContractOnly` axiom for it. The deep model is validated **== the real callee** out-of-band: axiom_check.py (G-AX) runs `np.take(shape, axis).prod()` on boundary+fuzz and asserts `prod(select(shape, axis)) == np.take(shape, axis).prod()` (mapping.md §3). |
| 5 | `return (total - missing - required_minimum) < 0` | `(... .prod() - mask.sum(axis) - min_count) < 0` | I + R | identical integer arithmetic and `< 0` comparison; the operands are the refined carriers of steps 2-4. Element-wise `< 0` over positions ↔ the per-position `Result()`. |

The discriminating content of the change — counting the **product** of all
reduced-axes sizes rather than a **single** axis's size — lives in step 4
(`total == prod(ToSeq(sizes))`). `model_prepatch.py` reverts step 4 to
`total = sizes[0]` (the single-axis `mask.shape[axis]` semantics, the only
expressible analog of the pre-patch code, which actually raised for a tuple
`axis`) and therefore **fails** the postcondition
`Result() == (prod(ToSeq(sizes)) - missing - required_minimum < 0)` whenever the
reduced block spans more than one element beyond the first axis — exactly the
spec sensing the change (G-DIFF). For a single reduced axis the two coincide
(`prod(sizes) == sizes[0]`), so the PASS_TO_PASS single-axis reductions are
preserved.

## No kind-3 (unexpressible-changed-op) steps

Every step is R, A-reference, or I. The operation that genuinely *changed* — the
element count `np.take(mask.shape, axis).prod()` — is modeled **deeply** (the
spelled-out `prod` fold, step 4, an **A-reference**), not behind an axiom about
the function under change. There is no consumed `@ContractOnly` axiom (the
proof depends on no opaque callee); the only callee involved
(`np.take(...).prod()`) is the changed expression itself, validated by G-AX as
the A-reference.

## verify(model) ⇒ resolved

`flag_too_few` verifies only if its result equals
`prod(ToSeq(sizes)) - missing - required_minimum < 0` (steps 4-5) for every
non-empty reduced-axis group. By R (step 1: `sizes == np.take(mask.shape, axis)`;
step 2: `missing == mask.sum(axis)`) and G-AX (step 4: the deep `prod` equals
the real `np.take(mask.shape, axis).prod()`, and the whole `null_mask` decision
matches the gold numpy expression on real masks), the verified function equals
the gold `null_mask` element at every output position, for one OR many reduced
axes. Deleting the early `raise` (gold part a) is the enabling control-flow edit
that lets the multi-axis case (`len(sizes) >= 2`) reach this expression at all;
the model admits `len(sizes) >= 2` directly, so it covers the previously-rejected
inputs. Therefore a model satisfying this spec, refined by the map above, is the
gold patch up to type refinement and the audited A-reference — and the gold
patch resolves (G-RESOLVE). The single trust point is the refinement fidelity of
this document (G-EQ) plus the A-reference soundness (G-AX); there is no consumed
axiom.
