# mapping.md — pydata__xarray-3095

## Symbol binding (file:line @ base_commit 1757dffac2)

| Lean symbol | Python | location |
|---|---|---|
| `implementation_copy` / `problem_spec_copy` / `correct_copy` | `IndexVariable.copy(deep, data=None)` along the `data is None` path | `xarray/core/variable.py:1919-1959` @ base_commit (edited hunk lines 1942-1949) |
| `IndexData` + the `dtype` clause | the index wrapper `PandasIndexAdapter` and its stored `self._dtype` re-attached on copy | `xarray/core/indexing.py:1230-1329` @ base_commit (added method, gold hunk line ~1322) |

The modeled function is `IndexVariable.copy`. On the `data is None` path it must
produce a new variable whose data wrapper has the SAME stored element type
(`dtype`) as the original. The gold patch achieves this by giving the wrapper a
`copy(deep)` method that rebuilds it as `PandasIndexAdapter(array, self._dtype)`
— re-attaching the recorded `self._dtype`. The pre-patch deep path rebuilt the
wrapper from the underlying sequence alone (`PandasIndexAdapter(self._data.array.copy(deep=True))`),
which re-infers the dtype from the (string→object) pandas index and so loses a
fixed-width unicode dtype.

## Why `dtype` can differ from the re-derived `native`

For a `<U3` unicode numpy array, the wrapper's `__init__` records
`self._dtype = <U3` (the dtype of the *original numpy array argument*). But
`safe_cast_to_index` turns the data into a pandas `Index` of dtype `object`.
Rebuilding the wrapper from that pandas index re-infers `object` — so the
re-derived element type (`native` in the Lean model) is `object`, while the
recorded element type (`dtype`) is `<U3`. The fix keeps `dtype`; the bug
substitutes `native`.

The shallow path (`deep=False`) reused `self._data` directly both pre- and
post-patch, so its dtype always survived — matching the issue note that
`DataArray.copy(deep=False)` is unaffected.

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Python | Lean | bijection |
|---|---|---|
| index values (1-D sequence of elements) | `values : List String` | each element ↦ its `str` form; length preserved |
| recorded wrapper dtype `self._dtype` | `dtype : Dtype` | `<Uw>` ↦ `unicode w`; `np.dtype('O')` ↦ `object`; `int64`/`float64`/… ↦ `other code` |
| dtype re-inferred from the pandas index of the values | `native : Dtype` | same encoding; for unicode values this is `object`, else equals `dtype` |
| `IndexVariable.copy(deep)` result | `result : IVar` | `.dims` ↦ `dims`, `.attrs` ↦ `attrs`, `._data._dtype` ↦ `data.dtype`, `._data.dtype` re-derivation ↦ `data.native`, values ↦ `data.values` |
| `deep` flag | `deep : Bool` | identity |

## Callee provenance + flag dependencies

- No callee axiom is consumed. The changed op (re-attaching the stored `dtype`)
  is the operation the patch introduces, so it is modeled DEEPLY (an A-reference
  validated by G-CONF against the real patched `IndexVariable.copy`), never
  axiomatized (§0.7).
- `self.array.copy(deep=...)` (pandas Index copy, unchanged) only duplicates vs
  shares the value sequence — content-identical either way — so it is reproduced
  concretely as identity on the value list; no axiom needed.
- Flag dependency: the bug manifests on `deep=True`; `deep=False` is unaffected.
  G-CONF fuzzes BOTH flag values so the discriminating (`deep=True`) and the
  always-correct (`deep=False`) configurations are both covered.

## G-CONF fuzz seed

`SEED = 20240711` (pinned in `conformance_check.py`).
