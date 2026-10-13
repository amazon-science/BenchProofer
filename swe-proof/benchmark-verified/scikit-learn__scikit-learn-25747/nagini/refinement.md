# refinement.md — scikit-learn__scikit-learn-25747

The operation-by-operation correspondence between `model.py`'s implementation
(the `wrap_in_container` impl region, with the `_copy_labels` helper and the
`Frame` carrier) and `patch.diff` (the gold patch). Each step is tagged **R**
(type refinement), **A-consumed** (the proof uses an axiom's `Ensures`),
**A-reference** (a deep model validated `== real callee` by axiom_check.py /
G-AX), or **I** (identical concrete operation). The claim: *any implementation
that verifies against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The change — `_wrap_in_pandas_container` (`sklearn/utils/_set_output.py:55-60`)

Gold hunk (the behavioural lines):
```
     if isinstance(data_to_wrap, pd.DataFrame):
         if columns is not None:
             data_to_wrap.columns = columns
-        if index is not None:
-            data_to_wrap.index = index
         return data_to_wrap
 
     return pd.DataFrame(data_to_wrap, index=index, columns=columns)
```
(plus a docstring line: `index` is ignored if `data_to_wrap` is already a
DataFrame — narrative only, no behaviour.)

| # | model.py impl op (`wrap_in_container`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `data_is_frame: bool` guarding the first branch | `isinstance(data_to_wrap, pd.DataFrame)` | R | the runtime type test ↔ its boolean value (mapping.md §2). |
| A2 | parameter `df: Frame` (fields `index`, `columns`) | `data_to_wrap` when it is a `pd.DataFrame` | R | `Frame` carries only the two touched label axes (mapping.md §2). |
| A3 | `columns`, `index : Optional[List[int]]` | the keyword args `columns`, `index` | R | `None` ↔ absent; a list ↔ a supplied label set as label codes (mapping.md §2). |
| A4 | `if columns is not None: df.columns = _copy_labels(columns)` | `if columns is not None: data_to_wrap.columns = columns` | R + I | identical control flow; `data_to_wrap.columns = columns` ↔ copying the supplied column labels onto `Frame.columns` (pandas builds a fresh column `Index`; value semantics, mapping.md §2). |
| A5 | **the supplied index is NOT applied** in the frame branch (no `df.index = …`); `Frame.index` is returned unchanged | the gold patch **deletes** `if index is not None: data_to_wrap.index = index` | I | identical: the post-patch frame branch performs NO index write, so the frame keeps its own row labels. This is the whole content of the fix; the model omits the same write. The discriminating postcondition `ToSeq(Result().index) == Old(ToSeq(df.index))` is exactly this. |
| A6 | `return df` | `return data_to_wrap` | I + R | the same object is returned; `Result() is df` (mapping.md §2). |
| A7 | not-a-frame branch: `Frame(_copy_labels(index) or _range_labels(nrows), _copy_labels(columns) or _range_labels(ncols), …)` | `return pd.DataFrame(data_to_wrap, index=index, columns=columns)` | R + I | identical control flow; constructing a fresh container stamped with the supplied row/column labels (value semantics) ↔ copying the supplied labels into a fresh `Frame`. **Each axis with NO supplied label set gets the default positional labelling `[0,1,…,k-1]`** (k = `nrows` / `ncols`), exactly mirroring `pd.DataFrame(..., index=None/columns=None)`'s default `RangeIndex(k)` (mapping.md §2). The model pins this with `_range_labels` + the `is_range(…, k)` postconditions, so the None corner is the gold RangeIndex, not an unconstrained value. |

The discriminating content of the change — *an already-a-container input keeps
its OWN row labels rather than being overwritten with the supplied index* —
lives in step A5. `model_prepatch.py` re-introduces the deleted write
(`if index is not None: df.index = _copy_labels(index)`) and **fails** the
postcondition `Implies(data_is_frame, ToSeq(Result().index) == Old(ToSeq(df.index)))`,
which is exactly the spec sensing the change (G-DIFF). The `_copy_labels` /
`_range_labels` helpers and the `opt_seq` / `is_range` spec functions are proof
scaffolding for the value semantics of the label copies and the default
positional labelling (R); they introduce no new behaviour. `_range_labels(k)`
materialises `[0,1,…,k-1]` and `is_range(s, k)` characterises that exact
sequence (length `k`, element `j` equals `j`), pinning each not-a-frame axis
that has no supplied label set to pandas's default `RangeIndex(k)`.

## B. No consumed axiom; one A-reference (the deep model itself)

There is **no `@ContractOnly` axiom** in this bundle and none is consumed: the
changed operation is a self-contained label-routing rule, modelled deeply by
`wrap_in_container`. The two "external" operations on the frame branch
(`data_to_wrap.columns = columns`) and on the array branch
(`pd.DataFrame(...)`) are the operations being modelled (R-refinements, §A),
not unchanged callees to axiomatize.

| # | model.py construct | repo op | tag | justification |
|---|---|---|---|---|
| B1 | the whole `wrap_in_container` deep model (label-routing logic) | the post-patch `_wrap_in_pandas_container` body | A-reference | the deep model is validated `==` the real post-patch helper by `axiom_check.py` (G-AX): it reconstructs the post-patch and pre-patch bodies over real `pandas`/`numpy` objects and asserts the model's resulting `(index, columns)` matches the post-patch helper over boundary + 2000 fuzz inputs, AND that the pre-patch body diverges on exactly a supplied index in the DataFrame branch (raising the reported length-mismatch ValueError in the aggregation case). NOT a consumed axiom — no `Ensures` of an opaque callee is used in the proof (mapping.md §3). |

## C. No kind-3 (unexpressible-changed-op) steps

Every step in §A is R or I. The one operation that genuinely *changed* — the
deletion of the index write so an already-a-container input keeps its own row
labels — is modelled **directly and deeply** (step A5: the model simply omits
the write, and the postcondition pins index preservation), not hidden behind an
axiom. There is no consumed axiom; the only `A-reference` (§B) is the deep model
validated against the real callee by G-AX.

## D. verify(model) ⇒ resolved

`wrap_in_container` verifies only if, on the already-a-container branch, the
returned container's row labels equal the container's OWN entry labels
(`ToSeq(Result().index) == Old(ToSeq(df.index))`, A5) regardless of any supplied
index, and the column labels are refreshed to the supplied set when given (A4)
or kept otherwise; and, on the not-a-container branch, the fresh container is
stamped with the supplied labels where given AND with the default positional
labelling `[0,1,…,k-1]` on every axis where no set is supplied (A7) — BOTH
corners of each axis are constrained:

- `index` supplied → `ToSeq(Result().index) == opt_seq(index)`;
  `index is None` → `is_range(ToSeq(Result().index), nrows)`
  (the RangeIndex the gold `pd.DataFrame(..., index=None)` builds).
- `columns` supplied → `ToSeq(Result().columns) == opt_seq(columns)`;
  `columns is None` → `is_range(ToSeq(Result().columns), ncols)`
  (the RangeIndex the gold `pd.DataFrame(..., columns=None)` builds — this is
  the corner the P2P test `test__wrap_in_pandas_container_column_errors` pins
  via its ndarray + raising-callable-columns call, which asserts
  `columns == range(X_np.shape[1])`).

There is no longer any unconstrained None corner, so no wrong impl can verify by
stamping an arbitrary label set there. By R (DataFrame ↔ `Frame`, label axis ↔
`List[int]`, `isinstance` ↔ `data_is_frame`, attribute write / constructor ↔
value copy, default `RangeIndex(k)` ↔ `is_range(…, k)`) the verified function
equals the post-patch `_wrap_in_pandas_container` on the tested inputs —
including the array+None corners; by G-AX the deep model equals the real
post-patch helper (B1, A-reference) over both corners of both axes and the
pre-patch body is the observed bug. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement — and the
gold patch resolves (G-RESOLVE). The only trust point is refinement fidelity
(this document, G-EQ) plus the label-code abstraction validated by G-AX; there
is no axiom-soundness trust point because no axiom is consumed.
