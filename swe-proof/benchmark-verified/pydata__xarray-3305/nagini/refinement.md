# refinement.md — pydata__xarray-3305

The operation-by-operation correspondence between `model.py`'s implementations
(the two contracted functions `reduce_result_metadata` and
`entrypoint_reduce_metadata`, plus the deep `resolve_keep` / `selected_meta`
model and the live `ambient_keep_default` axiom) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement), **A** (axiomatized callee
— split into **A-consumed**, the proof uses the axiom's `Ensures`, and
**A-reference**, a deep model validated == the real callee by axiom_check.py /
G-AX), or **I** (identical concrete operation). The claim: *any implementation
that verifies against this frozen spec, refined per the maps below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. Site 1 — the single-array reduction (`Variable.quantile`, `variable.py:1595`)

Gold hunk (signature + return):
```
- def quantile(self, q, dim=None, interpolation="linear"):
+ def quantile(self, q, dim=None, interpolation="linear", keep_attrs=None):
  ...
- return Variable(new_dims, qs)
+ if keep_attrs is None:
+     keep_attrs = _get_keep_attrs(default=False)
+ attrs = self._attrs if keep_attrs else None
+ return Variable(new_dims, qs, attrs)
```

`model.py` symbol for this site: `reduce_result_metadata(self_meta, keep_metadata)`.

| # | model.py impl op (`reduce_result_metadata`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `self_meta: List[int]` | `self._attrs` (the variable's attribute mapping) | R | metadata payload `dict`/`OrderedDict` ↔ `List[int]` code points; the patch copies/omits the whole payload, never an entry (mapping.md §2). Read-only ⇒ `Acc(list_pred(self_meta), 1/2)`. |
| A2 | parameter `keep_metadata: Optional[bool]` | `keep_attrs=None` parameter | I | identical three-valued flag. |
| A3 | `if keep is None: keep = ambient_keep_default()` | `if keep_attrs is None: keep_attrs = _get_keep_attrs(default=False)` | A-consumed | `ambient_keep_default` is the weakest contract on `_get_keep_attrs(default=False)` the proof needs: under the default ambient config it returns `False` (mapping.md §3.1). The proof consumes its `Ensures` to discharge the `resolve_keep(None)` branch. G-AX confirms it against the real resolver. |
| A4 | `result = []; if keep: result = list(self_meta)` | `attrs = self._attrs if keep_attrs else None` | R + I | the metadata selection (deep model `selected_meta`): keep ⇒ a faithful copy of the payload (`list(self_meta)` ↔ `self._attrs`); drop ⇒ empty (`[]` ↔ `None`, observationally the empty `.attrs`, mapping.md §2). The `if`/`else` control flow is identical. |
| A5 | `return result` (a `List[int]`) | `return Variable(new_dims, qs, attrs)` | R | the Variable wrapper carries `attrs` verbatim onto the result; `new_dims`/`qs` are the numeric reduction, computed identically pre/post-patch and observationally unchanged (mapping.md §2). The model isolates the only changed observable — the result metadata. |

The discriminating content of site 1 — the result metadata now *depends on*
the resolved flag instead of being unconditionally empty — lives in
`selected_meta(src, keep)` (model) ⇔ `attrs = self._attrs if keep_attrs else
None` (real). The pre-patch unconditionally returned `Variable(new_dims, qs)`
(metadata `None`); `model_prepatch_1.py` reproduces that (`result = []` always)
and **fails** the postcondition `ToSeq(Result()) == selected_meta(...,
resolve_keep(keep_metadata))` exactly when the flag resolves to True (G-DIFF).

## B. Site 2 — the container-level delegation (`Dataset.quantile`, `dataset.py:4694`)

Gold hunk (the per-variable delegation):
```
  variables[name] = var.quantile(
-     q, dim=reduce_dims, interpolation=interpolation
+     q,
+     dim=reduce_dims,
+     interpolation=interpolation,
+     keep_attrs=keep_attrs,
  )
```

`model.py` symbol for this site: `entrypoint_reduce_metadata(self_meta, keep_metadata)`.

| # | model.py impl op (`entrypoint_reduce_metadata`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `result = reduce_result_metadata(self_meta, keep_metadata)` | `var.quantile(q, dim=reduce_dims, interpolation=interpolation, keep_attrs=keep_attrs)` | I (caller↔callee under spec) + R | the delegation forwards the caller's flag **unchanged** to site 1. site 1 is itself under spec, so the caller's spec uses site 1's spec (not an axiom). `q`/`dim`/`interpolation` drive the numeric reduction (mapping.md §2, omitted as unchanged); the only modeled argument is the forwarded keep flag. |
| B2 | `return result` | `variables[name] = …` (the per-variable result placed in the new dataset) | R | the per-variable result's metadata is what the new dataset exposes for that variable; the F2P observes a single-variable DataArray, so this per-variable payload IS the observed `out.attrs`. |

The discriminating content of site 2 — the flag is *forwarded* rather than
defaulted — lives in passing `keep_metadata` to the delegation (model) ⇔
`keep_attrs=keep_attrs` (real). The pre-patch omitted the kwarg, so the
delegation received the default `None` and resolved it to "drop";
`model_prepatch_2.py` reproduces that (`reduce_result_metadata(self_meta,
None)`) and **fails** the postcondition `ToSeq(Result()) ==
selected_meta(..., resolve_keep(keep_metadata))` exactly when the *caller's*
`keep_metadata` is True but the forwarded `None` resolves to "drop" (G-DIFF).
This is an independently-fixed behaviour from site A: even with site A fixed,
omitting the forwarding (B) still drops the metadata — hence a separate failing
prepatch.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A, or I. The two operations that genuinely *changed* —
the metadata selection (site A) and the flag forwarding (site B) — are modeled
**deeply** (the spelled-out `resolve_keep` + `selected_meta` in the `pure`
region, consumed by both impls, and the explicit caller→callee delegation),
not hidden behind an axiom about a function under change. The only consumed
axiom, `ambient_keep_default` (**A-consumed**, step A3), covers an **unchanged**
callee (`_get_keep_attrs`) that the new code invokes only on the `None` branch.
There is no A-reference deep-model axiom here; G-AX additionally validates the
deep selection model end-to-end against the real `Variable.quantile` /
`DataArray.quantile` (axiom_check.py), which is a behavioural cross-check, not a
consumed axiom.

## D. verify(model) ⇒ resolved

`reduce_result_metadata` verifies only if its output metadata equals the exact
source-or-empty selection driven by the resolved flag (A4/A5), and
`entrypoint_reduce_metadata` verifies only if it forwards the caller's flag so
the per-array result honours it (B1). By R (attr-payload ↔ `List[int]`,
`Variable(...)`/`numeric` identities) the verified functions equal the gold
patch's metadata behaviour on the tested inputs; by A-consumed the `None`
branch uses the real `_get_keep_attrs` default (G-AX). Therefore a model
satisfying this spec, refined by the maps above, is the gold patch up to type
refinement and the one audited callee — and the gold patch resolves
(G-RESOLVE). The trust points are exactly the two of PLAN §1.1: axiom
soundness (G-AX) and refinement fidelity (this document, G-EQ).
