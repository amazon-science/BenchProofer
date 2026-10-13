# mapping.md — scikit-learn__scikit-learn-25747

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 2c867b8f822eb7a684f0d5c4359e4426e1c9cfe0`, states the type
abstraction, and records the provenance the deep-model fidelity check (G-AX)
rests on. **No `@ContractOnly` axiom is consumed**: the changed operation is a
self-contained label-routing rule, modelled deeply.

Repo file under change: `sklearn/utils/_set_output.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `wrap_in_container(data_is_frame, df, columns, index)` | `_wrap_in_pandas_container(data_to_wrap, *, columns, index=None)` — `sklearn/utils/_set_output.py:10` (body 44-62) | the modeled changed function (places transformed data into a labelled container) |
| `Frame` (fields `index`, `columns`) | a `pandas.DataFrame` — only its two touched label axes (`DataFrame.index`, `DataFrame.columns`) are modelled | minimal carrier of the touched facets |
| `Frame.index` | `pandas.DataFrame.index` (the row labels) | the discriminating facet (kept on the frame branch) |
| `Frame.columns` | `pandas.DataFrame.columns` (the column labels) | refreshed when a replacement set is supplied |
| `data_is_frame` (bool) | the runtime test `isinstance(data_to_wrap, pd.DataFrame)` (`_set_output.py:55`) | branch discriminator |
| `columns` / `index` (`Optional[List[int]]`) | the keyword args `columns` / `index` of `_wrap_in_pandas_container` | supplied label sets (read-only) |
| `opt_seq(x)` | spec helper: the label sequence of an optional supplied set (empty when absent) | pure spec only; no repo counterpart |
| `is_range(s, n)` | spec helper: `s` is the default positional labelling `[0,1,…,n-1]` | pure spec only; characterises pandas's default `RangeIndex(n)` |
| `_copy_labels(src)` | the value-copy of a label set into a fresh container axis | models pandas's materialisation of a passed label array into an `Index`/`columns`; pure value semantics |
| `_range_labels(n)` | the default positional labelling `[0,1,…,n-1]` built for an axis | models pandas's default `RangeIndex(n)` assigned when no label set is supplied for an axis of a freshly-built container |
| `nrows` / `ncols` (`int`) | the row / column count of the data payload being wrapped (`data_to_wrap.shape[0]` / `.shape[1]`) | sizes the default `RangeIndex` on each unsupplied axis of the fresh container |

The pre-patch repo lines the change removes (for the refinement audit; not
referenced from the consumer spec view): in the `isinstance(..., pd.DataFrame)`
branch, the two lines

```
        if index is not None:
            data_to_wrap.index = index
```

(`_set_output.py:58-59` @ base_commit).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `pandas.DataFrame` | `Frame` with fields `index`, `columns` | only the two label axes are observed by the tests; the data payload is not relabelled by this helper and is omitted. `df.index` ↔ `Frame.index`, `df.columns` ↔ `Frame.columns`. |
| a label axis (`DataFrame.index` / `.columns`, an `Index` of labels) | `List[int]` of label codes | `axis[k]` ↔ `field[k]`; `len(axis)` ↔ `len(field)`; an axis value inside a spec ↔ `PSeq[int]` via `ToSeq`. Labels are arbitrary hashables in pandas; the tests compare them by equality/order, which the integer-code abstraction preserves (a 1:1 encoding of labels to codes). |
| `isinstance(data_to_wrap, pd.DataFrame)` (`_set_output.py:55`) | the boolean parameter `data_is_frame` | the runtime type test is abstracted to the branch condition it computes (R: a runtime predicate ↔ its boolean value). |
| the keyword args `columns=None` / `index=None` | `Optional[List[int]]` (`None` ↔ absent) | `None` ↔ no supplied set; a list ↔ a supplied set of label codes. |
| `data_to_wrap.columns = columns` (`_set_output.py:57`) | `df.columns = _copy_labels(columns)` | pandas builds a fresh column `Index` from the passed array; the model copies the label values into the field. Observationally the column labels equal the passed values (value semantics; R). |
| `pd.DataFrame(data_to_wrap, index=index, columns=columns)` (`_set_output.py:62`) | `Frame(_copy_labels(index) or _range_labels(nrows), _copy_labels(columns) or _range_labels(ncols), …)` | constructing a fresh container stamped with the supplied row/column labels (value semantics; R). When an axis arg is `None`, pandas assigns the default `RangeIndex` sized to the payload (`range(nrows)` rows / `range(ncols)` columns); the model assigns the matching `[0,1,…,k-1]` via `_range_labels`, pinned by `is_range`. The P2P test `test__wrap_in_pandas_container_column_errors` exercises the columns=None corner (`assert columns == range(X_np.shape[1])`). |

`pandas`/`numpy` objects and `str` labels are inexpressible in Nagini's
fragment; the carrier is `Frame` + `List[int]` throughout, with values carried
by `PSeq[int]` via `ToSeq`.

## 3. Deep-model fidelity (no consumed axiom; checked by G-AX / axiom_check.py)

The whole behaviour of `_wrap_in_pandas_container` on the two branches the model
covers is **pure label-routing logic** — which label set ends up on which axis
of the returned container — modelled DEEPLY by `wrap_in_container`. There is no
opaque callee whose contract the proof consumes; the only "external" operations
are the two `pandas.DataFrame` attribute writes and the `pd.DataFrame(...)`
constructor, which are themselves the operations being modelled (R-refinements
in §2), not unchanged callees to axiomatize.

`axiom_check.py` (G-AX) therefore validates the deep model against the REAL
post-patch behaviour: it reconstructs the post-patch and pre-patch helper
bodies over genuine `pandas`/`numpy` objects (no sklearn import needed — the
logic is two attribute writes / one constructor) and asserts, over a boundary
battery + 2000 fuzz configurations:

- **Fidelity:** the deep model's resulting `(index labels, column labels)` equals
  the real POST-patch helper's, on already-a-DataFrame inputs (supplied index
  present/absent, of equal OR different length than the frame's own index;
  supplied columns present/absent) and on ndarray inputs (index/columns
  present/absent). The frame's OWN index is preserved on the frame branch.
- **Discriminating divergence:** the PRE-patch helper overwrites the frame's
  index with the supplied index on the DataFrame branch, diverging from the
  model / post-patch helper exactly when an index is supplied — and, in the
  aggregation scenario (supplied/original index LONGER than the aggregated
  frame's own index), the pre-patch write raises the reported
  `ValueError: Length mismatch`, while the post-patch helper succeeds.

The label-code abstraction (`str`/arbitrary labels ↔ `List[int]`) is the only
gap between the model and the real callee; the F2P test
(`test_set_output_pandas_keep_index`) and the updated
`test__wrap_in_pandas_container_dense_update_columns_and_index` observe the
index/columns by equality, which the 1:1 code encoding preserves. `pandas` is
the very stack the patched helper builds on and is present in the instance's
eval image; `axiom_check.py` imports only it, `numpy`, and the standard library.
Exit 0 iff every obligation holds.
