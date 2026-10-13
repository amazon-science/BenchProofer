# refinement.md — scikit-learn__scikit-learn-25102

The operation-by-operation correspondence between `model.py`'s implementation
(the `select_columns` impl region, the deep `kept_descs` compress, and the
`_copy_labels` carry-over helper) and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where the proof uses the axiom's `Ensures`, and **A-reference**,
where a deep model is validated == the real callee by axiom_check.py / G-AX),
or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies cleanly at
`base_commit` and is the real correctness oracle, G-RESOLVE).

## A. The column-selection site — `_transform()` (`sklearn/feature_selection/_base.py:92`)

The gold change rewrites the body of `SelectorMixin._transform` so that, for a
DataFrame input, the column subset is taken **on the original container** (which
preserves each column's own dtype and the row index) instead of on a
homogeneous NumPy array.

Gold hunk (the two behavioural deltas):
```
     if not mask.any():
         ...warn...
+        if hasattr(X, "iloc"):
+            return X.iloc[:, :0]
         return np.empty(0, dtype=X.dtype).reshape((X.shape[0], 0))
-    if len(mask) != X.shape[1]:
-        raise ValueError("X has a different shape than during fitting.")
-    return X[:, safe_mask(X, mask)]
+    return _safe_indexing(X, mask, axis=1)
```

The model abstracts a DataFrame as a `Frame` carrying its two touched facets:
its row labels (`index`) and its per-column descriptors (`descs`, one descriptor
per column — the dtype code). The boolean retention mask `self.get_support()` is
the `mask: List[int]` (0 = drop, 1 = keep). `select_columns(df, mask)` is the
column subset.

| # | model.py impl op (`select_columns`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `df: Frame` with fields `index: List[int]`, `descs: List[int]` | the DataFrame `X` (its `.index`, its per-column `.dtypes`) | R | the rich pandas DataFrame is modelled by the minimal class carrying only the two facets the F2P tests observe (`output.index`, `output.dtypes`); mapping.md §2. |
| A2 | `mask: List[int]` of per-column 0/1 flags, `len(df.descs) == len(mask)` | `mask = self.get_support()` — a boolean array of length `n_features_in_` | R | boolean array ↔ `List[int]` of 0/1; one flag per input column; mapping.md §2. |
| A3 | `new_descs == kept_descs(ToSeq(df.descs), ToSeq(mask))` — the per-column descriptors of the retained columns, in input order, each carried over unchanged (the deep compress in the `pure` region + the verified backward loop) | `_safe_indexing(X, mask, axis=1)` — selects the masked columns **on the DataFrame** | A-reference | the changed selection is modelled **deeply**: `kept_descs` (the spelled-out per-column compress) and the loop in `select_columns` ARE the column selection. There is no consumed axiom. The real callee `_safe_indexing(X, mask, axis=1)` on a DataFrame with a boolean mask dispatches to `_pandas_indexing` → `X.loc[:, mask]`, which keeps each retained column's **own** dtype (no homogenising NumPy coercion) — i.e. the per-column descriptors are compressed by the mask, in input order, each carried over. G-AX (axiom_check.py) runs the real `_safe_indexing` on heterogeneous-dtype frames and asserts `kept_descs == real per-column dtypes`. mapping.md §3.1. |
| A4 | `new_index == ToSeq(df.index)` — the result keeps the input's OWN row labels (the `_copy_labels` carry-over), for ANY number of retained columns including zero | the index of `_safe_indexing(X, mask, axis=1)` / `X.iloc[:, :0]` is `X`'s own index | A-reference + I | `_safe_indexing`'s `X.loc[:, mask]` and the empty-branch `X.iloc[:, :0]` both keep `X`'s row index. The model carries the index over verbatim (`_copy_labels`); G-AX asserts the real selection preserves `X.index` on both the non-empty and the empty mask. mapping.md §3.1. |
| A5 | the empty-mask case is the `i`-loop appending nothing → `new_descs == []` while `new_index` still `== ToSeq(df.index)` | `if hasattr(X, "iloc"): return X.iloc[:, :0]` (the new dataframe branch) | A-reference | when the mask retains no column, the model still returns a `Frame` with the input's row labels and zero columns; the real new branch `X.iloc[:, :0]` returns the same (a DataFrame keeping `X`'s index with 0 columns). The pre-patch `np.empty(0, dtype=X.dtype)` referenced the absent DataFrame `.dtype` and lost the dataframe nature (G-AX checks both). mapping.md §3.1. |
| A6 | (no node) — the model never raises a shape-mismatch | removal of `if len(mask) != X.shape[1]: raise ValueError(...)` | I | dead defensive check the patch deletes; the model's precondition `len(df.descs) == len(mask)` is the invariant that check guarded (mask length == #features). Removing an unreachable raise is observationally the identity on the tested inputs. mapping.md §2. |

The discriminating content of the change lives in two independently-observable
clauses, each with its own failing pre-patch skeleton (G-DIFF):

* **Behaviour 1 — per-column metadata.** `model_prepatch.py` reverts A3 to the
  NumPy homogenisation: every retained column is stamped with ONE shared
  descriptor (`homo`), mirroring `X[:, safe_mask(X, mask)]` coercing all columns
  to a single dtype. It **fails** the postcondition
  `ToSeq(Result().descs) == kept_descs(ToSeq(df.descs), ToSeq(mask))` whenever
  the retained columns have differing descriptors — exactly the heterogeneous-
  dtype case the F2P tests `test_output_dataframe` / `test_dataframe_output_dtypes`
  exercise.
* **Behaviour 2 — row labels.** `model_prepatch_2.py` reverts A4/A5 to a fresh
  positional row labelling `[0, 1, ..., n-1]` (the NumPy default index), mirroring
  the pre-patch returning a bare array / `np.empty(...).reshape(...)`. It **fails**
  the postcondition `ToSeq(Result().index) == ToSeq(df.index)` whenever the
  input's index is not exactly the positional range — the dataframe-index
  preservation the F2P empty-mask case (`step=0`) and the dtype tests rely on.

## B. The `_validate_data` / `transform` plumbing (gold hunks in `sklearn/base.py` and the `transform` head)

The gold patch also threads a `cast_to_ndarray` flag through `_validate_data`
and computes `preserve_X = hasattr(X, "iloc") and output_config_dense == "pandas"`
in `transform`, so that when pandas output is configured the DataFrame is **not**
cast to a NumPy array before `_transform` runs. This is pure **routing
plumbing**: it decides *whether `_transform` receives the original DataFrame or a
NumPy array*. Its entire observable purpose is to make the column-selection in
`_transform` (site A) operate on the DataFrame so the dtypes/index survive.

| # | model.py construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | the `select_columns` precondition that `df` is a labelled container (a `Frame`) — i.e. the modelled input is the DataFrame, not a coerced array | `cast_to_ndarray=not preserve_X` in `transform`; the guarded `if cast_to_ndarray: X = check_array(...)` in `_validate_data` | I (data-flow guard) | this plumbing only ensures the original DataFrame reaches `_transform`; it adds no new observable transformation of its own. The behaviour the F2P tests observe (dtype/index preservation) is produced entirely by site A operating on the DataFrame. Modelled implicitly by `select_columns` taking a `Frame` (the un-cast container). No separate failing prepatch is needed: with the cast still in place the input to site A would be a homogeneous array, which is precisely the homogenised-descriptors world `model_prepatch.py` already exhibits. mapping.md §3.2. |

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The operations that genuinely
*changed* — the column selection preserving per-column descriptors (A3) and the
row-label preservation including the empty branch (A4/A5) — are modelled
**deeply** (the spelled-out compress `kept_descs` and the index carry-over
`_copy_labels`, both consumed in `select_columns`), not hidden behind an axiom
about the function under change. There is **no consumed `@ContractOnly` axiom**;
the only kind-A relationships are **A-references**: the deep model is validated
== the real unchanged callee `_safe_indexing` (and the `X.iloc[:, :0]` branch) by
G-AX.

## D. verify(model) ⇒ resolved

`select_columns` verifies only if (A3) its output descriptors equal the exact
per-column compress of the input descriptors (each carried over, never
homogenised) and (A4/A5) it keeps the input's own row labels for any retained
count including zero. By R (DataFrame ↔ `Frame`; boolean mask ↔ `List[int]`;
dtype ↔ descriptor code) and by the B-plumbing routing the original DataFrame
into `_transform`, the verified selection equals
`_safe_indexing(X, mask, axis=1)` / `X.iloc[:, :0]` on the tested DataFrame
inputs; by G-AX the deep model `kept_descs` + index carry-over equals the real
`_safe_indexing` column selection (the A-reference) on heterogeneous-dtype
frames. Therefore a model satisfying this spec, refined by the map above, is the
gold patch up to type refinement and the audited unchanged callee — and the gold
patch resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1:
axiom/callee soundness (G-AX) and refinement fidelity (this document, G-EQ).
