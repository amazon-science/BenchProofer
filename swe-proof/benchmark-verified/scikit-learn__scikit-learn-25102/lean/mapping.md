# mapping.md — scikit-learn__scikit-learn-25102

## Symbol binding (file:line @ base_commit f9a1cf072da9d7375d6c2163f68a6038b13b310f)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_transform` / `problem_spec_transform` | `SelectorMixin.transform` composed with `SelectorMixin._transform` | `sklearn/feature_selection/_base.py:67-103` |
| `selectByMask` (pure helper) | the by-mask column selection `_safe_indexing(X, mask, axis=1)` (post-patch) / `X[:, safe_mask(X, mask)]` (pre-patch) | `_base.py:104` |
| `castAll` (pure helper) | the implicit `check_array` ndarray coercion inside `_validate_data(..., cast_to_ndarray=True)` that collapses a heterogeneous DataFrame to one common numpy dtype | `_base.py:82-90`, `sklearn/base.py:583` |
| `Column` (pure helper) | one input column: its label + its element dtype (the two observables the F2P tests check) | the DataFrame columns / their `.dtypes` |
| `TransformResult` (pure helper) | the transform output observed by the tests: `output.dtypes` (per-column name→dtype) and `output.shape[0]` (row count) | test_base.py `test_output_dataframe`, test_feature_select.py `test_dataframe_output_dtypes` |

The modeled function is the feature-selection `transform` (the `SelectorMixin`
public entry). Its observable behavior changes: with a native tabular input and
pandas output requested, the surviving columns must keep their **original
per-column dtypes** (and the row index / row count), rather than being collapsed
to one common numpy dtype by the unconditional ndarray validation.

### What the code does (base_commit, pre-patch)

```python
def transform(self, X):
    X = self._validate_data(X, dtype=None, accept_sparse="csr",
                            force_all_finite=..., reset=False)   # ALWAYS -> ndarray
    return self._transform(X)

def _transform(self, X):
    mask = self.get_support()
    if not mask.any():
        ...warn...
        return np.empty(0, dtype=X.dtype).reshape((X.shape[0], 0))
    if len(mask) != X.shape[1]:
        raise ValueError("X has a different shape than during fitting.")
    return X[:, safe_mask(X, mask)]
```

`_validate_data` unconditionally calls `check_array`, which converts a pandas
DataFrame to a single homogeneous numpy block — every column is coerced to one
common dtype (e.g. mixed `float32`/`category`/`float64` → `float64`). The later
`_SetOutputMixin` re-wraps the ndarray into a DataFrame, so the per-column dtype
information is already lost: the pandas output has the common dtype in every
selected column.

### What the patch changes

```python
# transform():
output_config_dense = _get_output_config("transform", estimator=self)["dense"]
preserve_X = hasattr(X, "iloc") and output_config_dense == "pandas"
X = self._validate_data(..., cast_to_ndarray=not preserve_X, reset=False)
return self._transform(X)

# _validate_data(): new cast_to_ndarray flag -> when False, X is NOT coerced.
# _transform():
if not mask.any():
    if hasattr(X, "iloc"):
        return X.iloc[:, :0]          # preserve dataframe index, 0 columns
    return np.empty(0, dtype=X.dtype).reshape((X.shape[0], 0))
return _safe_indexing(X, mask, axis=1)   # column-select, container-preserving
```

`preserve_X` is true exactly when the input is a DataFrame (`hasattr(X, "iloc")`)
AND the configured dense output is pandas. In that case the input is NOT cast to
an ndarray; `_safe_indexing(X, mask, axis=1)` selects the masked columns from the
**original** DataFrame, so each surviving column keeps its own dtype. Otherwise
(`cast_to_ndarray=True`, the unchanged path) the input is homogenised to one
common dtype before selection, as before.

### Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Python | Lean | bijection |
|---|---|---|
| `hasattr(X, "iloc")` | `isDataFrame : Bool` | the input is a native tabular container (a pandas DataFrame). |
| `_get_output_config("transform", estimator=self)["dense"] == "pandas"` | `outputPandas : Bool` | the configured dense output container is the native one (set via `set_output(transform="pandas")`). |
| the input DataFrame's columns `[(name, dtype) …]` in column order | `cols : List Column` (`name : Nat`, `dtype : Nat`) | each column label is a distinct integer identity; each dtype is a distinct integer identity. Only equality of names / dtypes is observed (matches `assert dtype == X.dtypes[name]`). |
| `X.shape[0]` (number of rows) | `nRows : Nat` | the row count, never changed by selection. |
| the single common numpy dtype produced by `check_array` homogenisation | `commonDtype : Nat` | the one dtype every column is coerced to when the DataFrame is converted to an ndarray block (e.g. `float64`). Distinct (in general) from the per-column dtypes — that distinctness is the content of the fix. |
| `self.get_support()` boolean mask (one flag per input column) | `mask : List Bool` | the per-column selection vector; `mask[i]=True` ⟺ column `i` is retained. |
| `transform(X).dtypes` (output columns, name→dtype, in order) + `transform(X).shape[0]` | `result : TransformResult` (`cols : List Column`, `nRows : Nat`) | the modeled observable: the surviving columns (name+dtype, input order) and the row count. |

### Abstracted (unchanged, not in the modeled observable)

The actual numerical values of the cells, `_get_support_mask` / `get_support`
(the source of `mask`, unchanged), `check_is_fitted`, sparse handling
(`accept_sparse="csr"`), and the `_SetOutputMixin` DataFrame re-wrapping plumbing
are unchanged by the patch and not modeled. The mask is an input to the modeled
step (it depends on the fitted selector, not on the dtype-preservation fix). The
F2P observable is column name→dtype identity and row count, which is exactly what
`TransformResult` carries.

## Callee provenance + flag deps

- `_get_output_config(...)["dense"]` — `sklearn/utils/_set_output.py`; a read-only
  config lookup. Modeled as the input boolean `outputPandas` (no callee axiom).
- `hasattr(X, "iloc")` — duck-type check for a pandas container. Modeled as the
  input boolean `isDataFrame` (no callee axiom).
- `_safe_indexing(X, mask, axis=1)` — `sklearn/utils/__init__.py`; selects the
  masked columns preserving the container. Modeled deeply as `selectByMask`
  (an A-reference would require it, but it is a structural by-flag filter over the
  input columns, so it is modeled in-line — no consumed axiom).
- `check_array` / `_validate_data(cast_to_ndarray=True)` homogenisation — modeled
  deeply as `castAll cols commonDtype` (collapse every column's dtype to the one
  common dtype). No consumed axiom: the operation that changed is modeled, not
  axiomatized.
- **Flag dependency:** dtype preservation happens ONLY under
  `isDataFrame && outputPandas` (both must hold). G-CONF fuzzes both booleans
  across all four combinations so the gate exercises the preserve and the
  homogenise paths.

## G-CONF fuzz seed

Pinned seed: **25102** (also in `conformance_check.py`). The R/I shadow of
`implementation_transform` is differential-tested against an in-process replica of
the patched `transform`/`_transform` behavior (preserve-or-homogenise under the
`isDataFrame && outputPandas` gate, then by-mask column selection) over ≥10⁵
fuzzed `(isDataFrame, outputPandas, cols, nRows, commonDtype, mask)` inputs plus
hand-picked edge cases.
