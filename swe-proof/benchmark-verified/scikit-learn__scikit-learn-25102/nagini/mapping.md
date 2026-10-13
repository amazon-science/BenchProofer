# mapping.md — scikit-learn__scikit-learn-25102

Binds every `model.py` symbol to its repository counterpart at
`base_commit = f9a1cf072da9d7375d6c2163f68a6038b13b310f`, states the type
abstraction, and gives the provenance of each kind-A relationship (here all
**A-reference**: the deep model validated == an unchanged callee by G-AX).

Repo files under change: `sklearn/feature_selection/_base.py` (the modelled
column-selection site) and `sklearn/base.py` (the `cast_to_ndarray` routing
plumbing, §3.2).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `select_columns(df, mask)` | `SelectorMixin._transform(self, X)` — `sklearn/feature_selection/_base.py:92` (body lines 94–104) | the modelled changed function (column subset of a feature selector) |
| `Frame` (fields `index`, `descs`) | the pandas `DataFrame` input `X` (its `.index` row labels and its per-column `.dtypes`) | minimal model of the touched DataFrame facets |
| `mask: List[int]` | `mask = self.get_support()` (`_base.py:94`) — a boolean array of length `n_features_in_` | per-column retention flags |
| `kept_descs(descs, mask)` *(deep model — A-reference)* | the column selection `_safe_indexing(X, mask, axis=1)` post-patch (unchanged callee `sklearn.utils._safe_indexing`, `sklearn/utils/__init__.py:285`, dispatching to `_pandas_indexing`, `:188`) | pure spec: the per-column-descriptor compress; the deep model of the column selection, validated `kept_descs == real per-column dtypes` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `_copy_labels(src)` | the row-index carry-over of `_safe_indexing` / `X.iloc[:, :0]` (the DataFrame keeps its own `.index`) | pure helper: faithful copy used to carry the input's row labels into the result |

The pre-patch repo constructs the change removes / replaces (for the refinement
audit, not referenced from the consumer spec view): `X[:, safe_mask(X, mask)]`
(`_base.py:104`, the homogenising NumPy column index), the
`np.empty(0, dtype=X.dtype).reshape((X.shape[0], 0))` empty branch
(`_base.py:101`, referencing the absent DataFrame `.dtype`), and the defensive
`if len(mask) != X.shape[1]: raise ValueError(...)` (`_base.py:102-103`).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| pandas `DataFrame` input `X` | `Frame` with `index: List[int]`, `descs: List[int]` | `X.index` ↔ `df.index` (row label codes); `X.dtypes[j]` ↔ `df.descs[j]` (per-column descriptor code); only the two F2P-observed facets are modelled |
| boolean support mask `self.get_support()` | `mask: List[int]` of 0/1 flags, `len == #columns` | `mask[j] != 0` ↔ the j-th feature is retained; `len(mask) == X.shape[1]` ↔ `len(df.descs) == len(mask)` (the precondition that made `_base.py:102`'s raise dead) |
| the selected DataFrame `_safe_indexing(X, mask, axis=1)` | `Frame` result with `descs == kept_descs(...)`, `index == df.index` | `result.dtypes[k]` ↔ `Result().descs[k]`; `result.index` ↔ `Result().index` |
| `str(...)`/`mark_safe`/`check_array` coercions — N/A here | — | the modelled behaviour is the column subset; the cast plumbing is §3.2 |
| dtype objects (`float32`, `category`, …) | distinct `int` descriptor codes | the F2P tests compare dtypes for equality only; an injective dtype↦int code suffices (G-AX compares the real dtypes by string, the model by code) |

`str`/object indexing is not used; the carrier is `List[int]` throughout and the
specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `kept_descs` + index carry-over deep model ↔ `_safe_indexing(X, mask, axis=1)` / `X.iloc[:, :0]` (A-reference)
**Callee:** `sklearn.utils._safe_indexing` (`sklearn/utils/__init__.py:285`). The
changed column selection is modelled **deeply** by the `@Pure` compress
`kept_descs` (over the per-column descriptors) plus the `_copy_labels` index
carry-over; there is **no consumed axiom**. The deep model is validated equal to
the real callee out-of-band by axiom_check.py (G-AX).

For a pandas DataFrame `X` and a boolean mask, `_safe_indexing(X, mask, axis=1)`:
`_determine_key_type(mask) == "bool"`; `hasattr(X, "iloc")` so it dispatches to
`_pandas_indexing(X, mask, "bool", axis=1)` (`:188`); there `key_dtype != "int"`
so `indexer = X.loc` and `axis=1` ⇒ it returns `X.loc[:, mask]`. A pandas
`.loc[:, bool_mask]` column slice **keeps each retained column's own dtype** (no
homogenising coercion) and **keeps `X`'s row index**. Hence the selection is
exactly the per-column compress

  `descs_out[k] = descs_in[(k-th position whose mask flag is set)]`, index unchanged,

which is what `kept_descs` / `_copy_labels` encode. The empty-mask branch
`return X.iloc[:, :0]` (the new `hasattr(X, "iloc")` guard) returns a DataFrame
keeping `X`'s index with zero columns — modelled by `select_columns` returning a
`Frame` with `new_descs == []` and `new_index == df.index`.

G-AX (axiom_check.py) runs the REAL `_safe_indexing` on heterogeneous-dtype
DataFrames (float32 / float64 / int32 / int64 / category mixtures), with
non-empty and empty masks and non-trivial indices, and asserts the deep model's
(index, kept-dtypes) == the real selection's (index, dtypes). It also exhibits
the **divergence** the bug introduced: the pre-patch `X[:, safe_mask(X, mask)]`
(modelled as `X.values[:, mask]`) homogenises all columns to one dtype, and the
pre-patch empty branch references the absent DataFrame `.dtype`. Docs: the
private-but-documented `_safe_indexing`; pandas `.loc` column selection
semantics.

### 3.2 The `cast_to_ndarray` routing plumbing (data-flow guard, tag I)
The gold patch adds a `cast_to_ndarray` parameter to
`BaseEstimator._validate_data` (`sklearn/base.py:495`, the guarded
`if cast_to_ndarray: X = check_array(X, input_name="X", **check_params)` at
`:577`) and computes, in `SelectorMixin.transform` (`_base.py:68`),
`preserve_X = hasattr(X, "iloc") and _get_output_config("transform",
estimator=self)["dense"] == "pandas"`, passing `cast_to_ndarray=not preserve_X`.
`_get_output_config` is the unchanged config reader (`sklearn/utils/_set_output.py:65`).

This plumbing is pure data-flow routing: it only decides whether `_transform`
receives the original DataFrame (when pandas output is configured) or a NumPy
array (otherwise). It introduces no new observable transformation; the
dtype/index preservation the F2P tests check is produced entirely by the column
selection at site A operating on the DataFrame. It is therefore modelled
implicitly — `select_columns` takes a `Frame` (the un-cast container) — and
tagged **I** in refinement.md §B (no axiom, no separate failing prepatch: with
the cast left in place the input to site A would be a homogeneous array, the very
homogenised-descriptors world `model_prepatch.py` already exhibits).

**Soundness check (G-AX):** `axiom_check.py` imports `pandas`, `numpy`, and the
repo's own unchanged `sklearn.utils._safe_indexing` (the very callee the patch
newly invokes), runs the real selection over a boundary battery (5 dtype
palettes × 3 indices × 4 masks each + empty masks) plus 1500 randomized fuzz
configurations, and asserts the deep model equals the real callee on every
observation. Exit 0 iff sound.
