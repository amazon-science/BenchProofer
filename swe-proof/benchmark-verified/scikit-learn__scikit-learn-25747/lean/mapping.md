# mapping.md — scikit-learn__scikit-learn-25747

## Symbol binding (file:line @ base_commit 2c867b8f822eb7a684f0d5c4359e4426e1c9cfe0)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_buildOutputContainer` / `problem_spec_buildOutputContainer` | `_wrap_in_pandas_container` (the routine that wraps a transformer's output into a DataFrame container) | `sklearn/utils/_set_output.py:10-62` |
| `containerResult` (pure helper) | the body deciding the returned container's columns / index / data | `_set_output.py:44-62` |
| `DataFrame` (pure helper) | a pandas `DataFrame` value, projected to its three observable parts (column labels, row index labels, cell data) | n/a |
| `InputData` (pure helper) | the `data_to_wrap` argument, by runtime category (scipy sparse / already a `DataFrame` / a plain array) | `data_to_wrap` parameter |

The modeled function is `_wrap_in_pandas_container`. It is the only function the
patch changes, and the only behavior the FAIL_TO_PASS test
(`test_set_output_pandas_keep_index`) and the changed PASS_TO_PASS test
(`test__wrap_in_pandas_container_dense_update_columns_and_index`) observe.

### What the function does (base_commit)

```python
def _wrap_in_pandas_container(data_to_wrap, *, columns, index=None):
    if issparse(data_to_wrap):
        raise ValueError("Pandas output does not support sparse data.")
    if callable(columns):
        try:    columns = columns()
        except Exception: columns = None
    pd = check_pandas_support(...)
    if isinstance(data_to_wrap, pd.DataFrame):
        if columns is not None:
            data_to_wrap.columns = columns
        if index is not None:               # <-- the removed clause (base_commit)
            data_to_wrap.index = index      # <-- the removed clause (base_commit)
        return data_to_wrap
    return pd.DataFrame(data_to_wrap, index=index, columns=columns)
```

- `issparse(...)` ⇒ raises (unchanged branch).
- The `columns` argument is `callable | array | None`; a callable is invoked and,
  if it raises, treated as `None`. This *resolution* is upstream of and orthogonal
  to the fix; it is folded into the resolved `Option` column labels that the
  modeled function receives.
- **DataFrame branch**: when `data_to_wrap` is already a DataFrame, its column
  labels are (optionally) replaced; at base_commit its row index is ALSO
  (optionally) replaced. The gold patch DELETES the index-replacement, so a
  DataFrame keeps its own row index regardless of the supplied `index`.
- **Array branch**: a fresh DataFrame is constructed from the data, the supplied
  `index` (else positional `range(n_rows)`) and `columns` (else `range(n_cols)`).
  Unchanged by the patch.

The patch's net observable effect: when `data_to_wrap` is a DataFrame, the
returned container's row index equals the *input DataFrame's own* index — never
the externally-supplied `index`.

### Lean modeling

- `DataFrame` carries the three observable parts the function reads/writes:
  `cols` (column labels), `idx` (row index labels), `data` (the cell payload).
- `InputData` is `data_to_wrap` by category: `.sparse`, `.dataframe df`,
  `.ndarray values`.
- The resolved column labels are `columns : Option (List String)` (the callable
  resolution + its exception-to-`None` fallback are folded in, per above). The
  external index is `index : Option (List Int)`.
- `containerResult` is the POST-PATCH decision; the impl is the `Id.run do`
  skeleton mirroring it (the index-replacement line absent). The pre-patch impl
  (`Solution_prepatch.lean`) re-introduces the index replacement
  (`if let some i := index then out := { out with idx := i }`), which is the
  base_commit behavior `data_to_wrap.index = index`.

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | bijection |
|---|---|---|
| `issparse(data_to_wrap)` true | `InputData.sparse` | identity (a scipy sparse input) |
| `isinstance(data_to_wrap, pd.DataFrame)` | `InputData.dataframe df` | identity |
| a plain `ndarray` / array-like | `InputData.ndarray values` | identity |
| `data_to_wrap.columns` | `DataFrame.cols : List String` | column labels, in order |
| `data_to_wrap.index` | `DataFrame.idx : List Int` | row index labels, in order (only identity/preservation matters to the fix) |
| the cell values | `DataFrame.data : List (List Int)` | the payload, unchanged by the function |
| resolved `columns` arg (`array | None`) | `columns : Option (List String)` | `None ↔ none`; an array of labels ↔ `some labels` |
| `index` arg (`array | None`) | `index : Option (List Int)` | `None ↔ none`; an array ↔ `some labels` |
| `range(n_cols)` default columns | `ndColumns values` | `["0","1",…]` (positional) |
| `range(n_rows)` default index | `ndIndex values` | `[0,1,…]` (positional) |
| `raise ValueError("…sparse…")` | `Except.error _` | the sparse-rejection branch |
| returned DataFrame | `Except.ok (df : DataFrame)` | identity |

## Callee provenance + flag dependencies

- **No consumed callee axiom; no A-reference.** The behavior the patch changes —
  which row index the wrapped container carries when the input is a DataFrame — is
  modeled DEEPLY and structurally over the observable parts of the inputs.
  SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled changed decision, so the
  `axioms` region is empty and **G-AX skips**.
- `check_pandas_support(...)` merely imports pandas (it returns the `pd` module);
  it has no effect on the returned container's value and is not modeled.
- `issparse(...)` and the `callable(columns)` resolution are UNCHANGED by the
  patch and orthogonal to the index fix: the sparse case is modeled as the
  `.sparse` category; the columns resolution is folded into the resolved
  `Option (List String)` the function receives. Neither leaves an output
  component free — `result` is pinned in full by `containerResult`.

## G-CONF fuzz seed

Pinned LCG seed: **25747** (see `conformance_check.py` `SEED`). Corpus:
randomized `InputData` crossing all three categories, with emphasis on the
discriminating category — a `.dataframe` input with a supplied `index` that
differs from the frame's own index (the post-patch container must keep the
frame's own index). Plus control inputs hitting the sparse branch, the
columns-replacement sub-case, and the array branch (supplied vs default
index/columns), over ≥1e5 fuzzed inputs. The R/I shadow of
`implementation_buildOutputContainer` is diffed against an in-process replica of
the POST-PATCH logic. Hand-picked edge cases pin the discriminator: a DataFrame
input with `index = some [other…]` ⇒ result index equals the input frame's index,
not the supplied one.
