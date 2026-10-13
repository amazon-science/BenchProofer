# refinement.md — astropy__astropy-13236

Operation-by-operation correspondence between `implementation_columnForTableData`
(Solution.lean impl region) and `patch.diff` (the POST-PATCH
`Table._convert_data_to_col` class-selection chain). Tags: **R** type
refinement, **A-consumed** proof uses an axiom, **A-reference** deep model
validated == real callee, **I** identical concrete op.

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `if inp.isColumn then return inp.columnInputResult` | `if isinstance(data, Column): col_cls = self._get_col_cls_for_table(data)` (then build) | R |
| 2 | `else if inp.isMixin then return inp.dataMixinClass` | `elif data_is_mixin: col = col_copy(...)/data; ... return col` (class preserved) | R |
| 3 | `else if inp.data0IsMixin then return inp.seqMixinResult` | `elif data0_is_mixin: try col = data[0].__class__(data); return col / except: data=np.array(...,object); col_cls = self.ColumnClass` | R |
| 4 | `else if inp.isMaskedArray then return inp.tableMaskedColumn` | `elif isinstance(data, (np.ma.MaskedArray, Masked)): col_cls = masked_col_cls` | R |
| 5 | `else if inp.isNone then return inp.tableColumnClass` | `elif data is None: data = np.array(None); col_cls = self.ColumnClass` | R |
| 6 | `else if !inp.hasDtype then (if inp.seqConvMasked then tableMaskedColumn else tableColumnClass)` | `elif not hasattr(data,'dtype'): data=_convert_sequence_data_to_array(...); col_cls = masked_col_cls if isinstance(data, np.ma.MaskedArray) else self.ColumnClass` | R |
| 7 | `else return inp.tableColumnClass` | final `else: col_cls = self.ColumnClass` | R |
| — | (no op — the removed clause is absent) | the DELETED `if not isinstance(data,Column) and not data_is_mixin and isinstance(data,np.ndarray) and len(data.dtype)>1: data = data.view(NdarrayMixin); data_is_mixin = True` | I (deletion: a structured plain array now falls through ops 4/6/7 instead of being forced to a mixin) |

Notes:

- **Every step is R or I — no A.** The class decision is modeled DEEPLY over the
  observable input flags; SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled
  changed decision. The `axioms` region is empty; **G-AX skips**.
- The R tag on ops 1–7 is the *carried-observation* refinement: the result of
  each UNCHANGED upstream sub-decision (`_get_col_cls_for_table`, the
  sequence-of-mixin construction incl. its object-array fallback,
  `_convert_sequence_data_to_array`'s masked-ness, the table's `ColumnClass` /
  `masked_col_cls`, the preserved class of an already-mixin value) is a field of
  `ConvInput` rather than re-derived. These are orthogonal to the structured-array
  fix and unchanged by the patch; the bijection is the class↔`ColClass` map in
  mapping.md. None of them leaves an output component free: `result` is fully
  pinned to `convResultClass inp`.
- The **fix itself** is op-"—": removing the early force-to-mixin clause. Its
  effect is captured by the absence of any leading mixin override in the impl,
  exactly mirroring the deleted lines. The pre-patch impl
  (`Solution_prepatch.lean`) re-introduces it as a leading
  `if !isColumn && !isMixin && isNdarray && numDtypeFields > 1 then return
  ndarrayMixin`, which is behaviourally identical to `data.view(NdarrayMixin)`
  followed by the `data_is_mixin` return branch.
- **G-CONF** mechanically refutes the R/I legs (no A legs): the Python shadow of
  the impl is diffed against the post-patch selection over ≥1e5 fuzzed inputs.
