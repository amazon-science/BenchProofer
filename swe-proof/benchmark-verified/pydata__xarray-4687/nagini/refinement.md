# refinement.md — pydata__xarray-4687

The operation-by-operation correspondence between `model.py`'s implementation
(the `select_payload` impl region, the deep index-1 selection, and the live
`default_mode_drops` axiom) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where the proof uses the axiom's `Ensures`, and **A-reference**,
where a deep model is validated == the real callee by axiom_check.py / G-AX), or
**I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The changed function — `where()` (`xarray/core/computation.py:1730`)

Gold hunks (three): (1) add the `keep_attrs=None` parameter; (2) when
unspecified, resolve it through `_get_keep_attrs(default=False)`, and when
PRESERVE (`keep_attrs is True`), install the combiner `lambda attrs, context:
attrs[1]`; (3) thread `keep_attrs=keep_attrs` into the `apply_ufunc` call.

```
- def where(cond, x, y):
+ def where(cond, x, y, keep_attrs=None):
      ...
+     if keep_attrs is None:
+         keep_attrs = _get_keep_attrs(default=False)
+     if keep_attrs is True:
+         keep_attrs = lambda attrs, context: attrs[1]
      return apply_ufunc(
          duck_array_ops.where, cond, x, y,
          join="exact", dataset_join="exact", dask="allowed",
+         keep_attrs=keep_attrs,
      )
```

| # | model.py impl op (`select_payload`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `mode: int` ∈ {0,1} | the `keep_attrs` argument value `None`/`True` | R | `None ↔ 0` (DEFAULT, unspecified), `True ↔ 1` (PRESERVE). mapping.md §2. The general bool/str/callable forms are outside the modeled domain (`Requires(mode==0 or mode==1)`); the F2P test uses only `None` and `True`. |
| A2 | parameter `attrs: List[List[int]]` len 3, index 1 = first-choice operand | the positional attrs list `[cond.attrs, x.attrs, y.attrs]` that `apply_ufunc` forms from `cond, x, y` and hands to `merge_attrs` | R | dict payload ↔ `List[int]` (content identity); positional order index 0=cond, 1=x, 2=y. mapping.md §2. |
| A3 | `if mode == 0 and default_mode_drops(): return []` (empty payload) | `if keep_attrs is None: keep_attrs = _get_keep_attrs(default=False)` → `False` → `apply_ufunc` maps to `"drop"` → `merge_attrs` returns `{}` | A-consumed | the unspecified mode resolves through the unchanged option reader; under the default global option `_get_keep_attrs(default=False)` is `False`, mapped to the dropping behaviour (`{}`). The proof consumes the axiom's `Ensures(Result() == True)` (drops). mapping.md §3.1; G-AX checks the real callee. The empty list ↔ `{}` by R. |
| A4 | PRESERVE branch: result `== attrs[1]` (copy of the first-choice operand's payload) computed by the verified copy loop | `if keep_attrs is True: keep_attrs = lambda attrs, context: attrs[1]`, then `merge_attrs(callable)` returns `attrs[1]` (= x.attrs) | A-reference | the changed combine operation is modeled **deeply**: the index-1 selection IS the behaviour. No consumed `merge_attrs` axiom — the proof never depends on one. The deep model is validated **== the real callee** out-of-band: G-AX runs `merge_attrs` with the combiner on boundary+fuzz payload lists and asserts the result equals positional index 1, plus end-to-end `xr.where(...,keep_attrs=True).attrs == x.attrs`. mapping.md §3.2. |
| A5 | `result` returned (a `List[int]`) | the merged `attrs` dict installed on the `apply_ufunc` output | R | dict payload ↔ `List[int]` content; the F2P `test_where_attrs` compares the result's `.attrs` dict, which equals x's. |

The discriminating content of the change — under PRESERVE the surviving payload
is the **first-choice operand's, positional index 1** (x), not index 0 (cond)
nor index 2 (y), nor empty — lives in step A4 (`ToSeq(Result()) ==
ToSeq(attrs[1])`). The pre-patch `where` never threaded the mode into the
combine step, so the result always dropped attrs; `model_prepatch.py` reproduces
that (returns the empty payload unconditionally) and **fails** the postcondition
`Implies(mode == 1, ToSeq(Result()) == ToSeq(attrs[1]))`, which is exactly the
spec sensing the change (G-DIFF).

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, A-reference, or I. The one operation that
genuinely *changed* — installing the attribute combiner so the first-choice
operand's payload survives — is modeled **deeply** (the spelled-out index-1
selection in `select_payload`, step A4, an **A-reference**), not hidden behind
an axiom about the changed function. The only consumed axiom,
`default_mode_drops` (**A-consumed**, step A3), covers an **unchanged** callee
(`_get_keep_attrs`/`_get_boolean_with_default`) the new code invokes when the
mode is unspecified; the combiner's `merge_attrs` appears only as the
**A-reference** that G-AX validates the deep model against.

## C. verify(model) ⇒ resolved

`select_payload` verifies only if (A4) its PRESERVE output equals the payload at
positional index 1 (the first-choice operand) and (A3) its DEFAULT output is
empty. By R (dict payload ↔ `List[int]`, positional order, `None/True ↔ 0/1`)
the verified selection equals what the gold `where` produces: PRESERVE installs
`lambda attrs, context: attrs[1]` and `merge_attrs` returns `attrs[1]` (x's
attrs), while the unspecified mode resolves to drop. By G-AX the deep index-1
model equals the real `merge_attrs(callable)` (A-reference) and the real
`_get_keep_attrs(default=False)` meets the `default_mode_drops` axiom under the
default option (A-consumed). Therefore a model satisfying this spec, refined by
the map above, is the gold patch up to type refinement and audited callees — and
the gold patch resolves (G-RESOLVE). The trust points are exactly the two of
PLAN §1.1: axiom soundness (G-AX) and refinement fidelity (this document, G-EQ).
