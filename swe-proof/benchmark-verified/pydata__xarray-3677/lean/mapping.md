# mapping.md — pydata__xarray-3677

## Symbol binding (file:line @ base_commit ef6e6a7b86f8479b9a1fecf15ad5b88a2326b31e)

| Lean | Python | file:line @ base_commit |
|---|---|---|
| `implementation_merge` / `problem_spec_merge` / `correct_merge` | `Dataset.merge` (the method) | `xarray/core/dataset.py:3547-3616` (the added coercion lands at line 3607, just before the `dataset_merge_method(...)` call at 3608) |
| `datasetOfArray : DataArray → Dataset` | `DataArray.to_dataset()` (no `dim`, default `name`) → `_to_dataset_whole` | `xarray/core/dataarray.py:490` (`to_dataset`), `:462` (`_to_dataset_whole`) |
| `mergeDatasets : Dataset → Dataset → Except MergeErr Dataset` | the dataset-to-dataset merge guts: `dataset_merge_method(self, other, …)` then `self._replace(**merge_result._asdict())` | `xarray/core/merge.py:798` (`dataset_merge_method`) → `merge_core` `:548`; `_replace` in `xarray/core/dataset.py` |
| `MergeErr` | `xarray.core.merge.MergeError` (a conflict during merge) | `xarray/core/merge.py` (`class MergeError`) |

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Lean type | Python | note |
|---|---|---|
| `MergeOther = .ds Dataset \| .da DataArray` | the second argument `other : "CoercibleMapping"`, restricted to the two runtime shapes the fix's `isinstance(other, xr.DataArray)` distinguishes | `.da` ⇔ `isinstance(other, xr.DataArray)` true; `.ds` ⇔ an `xr.Dataset` (isinstance false). Dict-like `CoercibleMapping` operands are out of scope of this fix (pre-patch already handled them; the bug is DataArray-only). |
| `Dataset` (opaque, `Nonempty`) | `xarray.core.dataset.Dataset` | opaque carrier; only shape used is "a dataset value" |
| `DataArray` (opaque, `Nonempty`) | `xarray.core.dataarray.DataArray` | opaque carrier; only shape used is "a single named array" |
| `Except MergeErr Dataset` | a `Dataset` on success, or a raised `xarray.MergeError` | `.ok` = merged dataset; `.error` = the conflict error |

## Callee provenance + flag deps

- `datasetOfArray` (A-reference): `DataArray.to_dataset()` called with NO `dim`
  argument (the fix's `other.to_dataset()`), so it routes to `_to_dataset_whole`
  — the "one variable named `self.name`" dataset. Flag: `dim=None` (default).
  UNCHANGED by the patch. G-AX property P1/P2.
- `mergeDatasets` (A-reference): `dataset_merge_method` + `Dataset._replace`, the
  exact guts the method invoked BEFORE the fix and still invokes after, called
  with the method's default kwargs for the F2P path
  (`overwrite_vars=frozenset(), compat="no_conflicts", join="outer",
  fill_value=dtypes.NA`). UNCHANGED by the patch. G-AX property P2/P3.
- No CONSUMED axiom: `correct_merge` closes by `cases other <;> rfl`. The opaque
  signatures suffice; no `_prop` axiom is asserted or consumed.

## G-CONF fuzz seed

Pinned seed: **3677** (also used by `axiom_check.py`). G-CONF is a skip stub for
this instance (`conf_skip = true`) — the impl region is all-A-reference, no R/I
computational leg to differential-test; the seed is recorded for reproducibility
of the G-AX fuzz.
