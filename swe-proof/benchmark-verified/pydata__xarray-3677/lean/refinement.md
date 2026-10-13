# refinement.md — pydata__xarray-3677

Each operation of `implementation_merge` mapped to its `patch.diff` counterpart.
Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's property),
**A-reference** (deep model validated == real callee by G-AX), **I** (identical
concrete op).

The gold patch adds exactly one line to `Dataset.merge` — a coercion of the
second operand — immediately before the (unchanged) call to the dataset merge
guts:

```python
other = other.to_dataset() if isinstance(other, xr.DataArray) else other
merge_result = dataset_merge_method(self, other, ...)
return self._replace(**merge_result._asdict())
```

| # | Lean impl op | patch.diff / repo counterpart | tag | note |
|---|---|---|---|---|
| 1 | `match other with … \| .da a => datasetOfArray a \| .ds d => d` (the `let other'`) | `other = other.to_dataset() if isinstance(other, xr.DataArray) else other` — THE fix | A-reference | The added coercion. `other : "CoercibleMapping"` is modeled as the sum `MergeOther = Dataset ⊕ DataArray` (R on the operand type — see mapping.md). The `isinstance(other, xr.DataArray)` dispatch is the two-constructor `match`; `.to_dataset()` is the unchanged callee `datasetOfArray`. Validated == real `to_dataset()` by G-AX (P1/P2). |
| 2 | `return mergeDatasets self other'` | `merge_result = dataset_merge_method(self, other, …); return self._replace(**merge_result._asdict())` | A-reference | UNCHANGED merge guts (`dataset_merge_method` + `_replace`), invoked on the coerced operand exactly as before. Modeled as `mergeDatasets : Dataset → Dataset → Except MergeErr Dataset` (success = merged dataset; error = the `MergeError` a conflict raises). Validated == real merge guts by G-AX (P2/P3). |

Operand-type refinement (R), recorded here and in mapping.md: Python's runtime
union `Dataset | DataArray` (the two isinstance-distinguished cases the method
must handle) ↔ Lean `inductive MergeOther`. The bijection is total on the two
shapes the fix distinguishes; other `CoercibleMapping` inputs (dict, etc.) are
out of scope of THIS fix (the pre-patch already handled dicts; the bug is
DataArray-only, per the issue and F2P test).

No **A-consumed** rows ⇒ no consumed callee property axiom; `correct_merge`
closes by case analysis (`cases <;> rfl`) — the contract is stated directly over
the opaque callees. Op 1 and op 2 are both **A-reference**; there is no **R**
(computational) or **I** leg ⇒ the impl region is all-A-tagged ⇒
`conf_skip = true` (G-CONF skip stub). G-AX validates the two A-reference callees
against the real repo callees.

## Prepatch discriminator

`Solution_prepatch.lean` drops op 1 (the coercion). A dataset operand still merges
normally (`.ds d => mergeDatasets self d`), but a single named array is not read
as its one-variable dataset — it is treated as an operand the dataset-to-dataset
merge cannot consume, yielding `Except.error …` (mirroring the real
`AttributeError: 'DataArray' object has no attribute 'items'` the pre-fix path
raises inside `coerce_pandas_values`). On the `.da a` branch the spec demands
`result = mergeDatasets self (datasetOfArray a)`; the buggy impl yields
`Except.error …`, which is not equal to the successful merge outcome — the
carried gold proof cannot close (`rfl` fails on the `.da` case). G-DIFF satisfied.
This is exactly the F2P scenario `test_merge_dataarray`:
`ds.merge(da) == xr.merge([ds, da])`.
