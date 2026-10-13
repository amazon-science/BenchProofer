# refinement.md — scikit-learn__scikit-learn-25747

Operation-by-operation correspondence between `implementation_buildOutputContainer`
(Solution.lean impl region) and `patch.diff` (the POST-PATCH
`_wrap_in_pandas_container`). Tags: **R** type refinement, **A-consumed** proof
uses an axiom, **A-reference** deep model validated == real callee, **I**
identical concrete op.

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `match input with \| .sparse => return Except.error "…sparse…"` | `if issparse(data_to_wrap): raise ValueError("Pandas output does not support sparse data.")` | R |
| 2 | `\| .dataframe df => let mut out := df` | `if isinstance(data_to_wrap, pd.DataFrame): …` (the input frame is the result base) | R |
| 3 | `if let some c := columns then out := { out with cols := c }` | `if columns is not None: data_to_wrap.columns = columns` | R |
| 4 | (no op — the index-replacement is absent) | the DELETED `if index is not None: data_to_wrap.index = index` | I (deletion: a DataFrame keeps its own row index instead of being overwritten by the supplied `index`) |
| 5 | `return Except.ok out` | `return data_to_wrap` | I |
| 6 | `\| .ndarray values => let cols := … let idx := … return Except.ok { cols, idx, data := values }` | `return pd.DataFrame(data_to_wrap, index=index, columns=columns)` (supplied else positional defaults) | R |

Notes:

- **Every step is R or I — no A.** The wrapping rule is modeled DEEPLY over the
  observable parts of the inputs (the data's category and, when it is already a
  table, its own column/index/payload, plus the optional supplied column labels
  and row index). SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled changed
  decision. The `axioms` region is empty; **G-AX skips**.
- The R tag on op 1 is the sparse-rejection refinement: `raise ValueError`
  ↔ `Except.error` (mapping.md). Op 3's R is the `columns`-resolution
  refinement: the callable-invocation + exception-to-`None` fallback is upstream
  of and orthogonal to the index fix, folded into the resolved
  `columns : Option (List String)` the modeled function receives. Op 6's R is the
  fresh-table construction with the supplied-or-positional `index`/`columns`
  (`ndIndex`/`ndColumns`), unchanged by the patch.
- The **fix itself** is op #4: removing the `data_to_wrap.index = index`
  assignment, so the returned container keeps the input DataFrame's own row index.
  Its effect is captured by the ABSENCE of any index-write in the `.dataframe`
  branch of the impl, exactly mirroring the deleted lines. The pre-patch impl
  (`Solution_prepatch.lean`) re-introduces it as
  `if let some i := index then out := { out with idx := i }`, behaviourally
  identical to `data_to_wrap.index = index`. This is the only independently-fixed
  behavior, so there is one prepatch variant.
- **No changed-inexpressible op.** Cell payload and column labels are carried
  structurally; only the index-preservation vs index-overwrite distinction is
  soundness-critical and it is modeled exactly (the `.dataframe` branch keeps
  `df.idx`).
- **G-CONF** mechanically refutes the R/I legs (no A legs): the Python shadow of
  the impl is diffed against an in-process replica of the post-patch logic over
  ≥1e5 fuzzed inputs, emphasizing the discriminating case (a DataFrame input with
  a supplied index that differs from the frame's own index).
