# mapping.md — astropy__astropy-13236

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 6ed769d58d89380ebaa1ef52b300691eefda8928`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and gives the
provenance of each modeled callee.

Repo file under change: `astropy/table/table.py` (method
`Table._convert_data_to_col`).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `classifyColumn (input : InputShape) (tableIsMasked : Bool)` | the column-class selection in `Table._convert_data_to_col` — `astropy/table/table.py:1179` (selection block lines 1244–1313) | the modeled classification: which column class an input value is wrapped in |
| `InputShape` (inductive) | the disjoint cases of the value `data` reaching the selection block (after the mixin-handler step at 1230–1240) | the only input distinctions the selection reacts to |
| `tableIsMasked : Bool` | the host table's masked-ness — whether `self.ColumnClass` is `MaskedColumn` (`table.py:390-397` `ColumnClass` property; drives both `masked_col_cls` at 1219–1221 / used at 1294, 1310 and the trailing `else: col_cls = self.ColumnClass` at 1313, and the `_get_col_cls_for_table` upgrade at 1266) | whether the host table wraps every array-like value as a masked column |
| `ColumnKind` (inductive result) | the value `col_cls` finally chosen (or the early `return col` mixin path) — `table.py:1266,1278,1284,1294,1298,1310,1313` | the resulting column class kind |

The selection block, in source order at base_commit (the **pre-image** still
contains the structured-ndarray branch the patch removes, lines 1244–1250):

```python
        # (pre-image only — REMOVED by patch.diff)
        if (not isinstance(data, Column) and not data_is_mixin
                and isinstance(data, np.ndarray) and len(data.dtype) > 1):
            data = data.view(NdarrayMixin)
            data_is_mixin = True

        ...                                              # name precedence (no col_cls effect)
        if isinstance(data, Column):
            col_cls = self._get_col_cls_for_table(data)  # -> upgraded to MaskedColumn
                                                         #    when table masked, else Column
        elif data_is_mixin:
            col = col_copy(...) ...; return col          # -> a mixin column (e.g. NdarrayMixin)
        elif data0_is_mixin: ...
        elif isinstance(data, (np.ma.MaskedArray, Masked)):
            col_cls = masked_col_cls                     # -> MaskedColumn (any table)
        elif data is None: ...
        elif not hasattr(data, 'dtype'): ...
        else:
            col_cls = self.ColumnClass                   # -> MaskedColumn iff table masked,
                                                         #    else Column
```

The patched (post-image) selection is the same block with the structured-ndarray
`if` deleted. `patch.diff` is the gold patch **verbatim** (G-RESOLVE).

Note the two table-masked-ness-sensitive sinks: `masked_col_cls` is
`MaskedColumn` for BOTH masked and unmasked tables (it exists precisely so a
mask-carrying value is preserved even in an unmasked table), while
`self.ColumnClass` / `_get_col_cls_for_table` yield `MaskedColumn` only when
the table itself is masked. The model therefore takes `tableIsMasked` as a
second input; collapsing it away was the G-PANEL-2 unfaithfulness this file's
previous revision had (a masked table wraps a plain array / structured array /
existing Column as `MaskedColumn`, which the one-input model called
`.columnKind`).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean domain
and the Python repo. A wrong entry surfaces as spurious G-CONF disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the value `data` reaching the selection block, reduced to the distinctions the block tests (`isinstance Column`, already-a-mixin, structured-ndarray-ness, masked-array-ness, plain-array-ness) | `InputShape` (inductive) | an existing `Column` (non-masked) ↔ `.alreadyColumn`; a value already a valid mixin for the table (`data_is_mixin` True at block entry, e.g. an explicit `.view(NdarrayMixin)`) ↔ `.alreadyMixin`; an unmasked numpy `ndarray` with `len(dtype) > 1` (multi-field structured dtype) ↔ `.structuredPlain`; a `np.ma.MaskedArray` with multi-field dtype ↔ `.structuredMasked`; a non-structured `np.ma.MaskedArray`/`Masked` ↔ `.plainMasked`; any other plain array value routed to the trailing `else` ↔ `.plainOther`. The cases are the disjoint inputs the F2P tests exercise; cases the issue/tests never reach (`None`, mixin-handler products, sequences-of-mixins, non-dtype scalars/sequences) are out of scope and not modeled. For a `.structuredPlain`/`.structuredMasked` input, `data_is_mixin` is `False` at entry (a bare structured array is not a mixin for the table — `_is_mixin_for_table` returns False), which is exactly the precondition the deleted branch tested. |
| the host table's masked-ness: `self.ColumnClass is MaskedColumn` (set by `Table(masked=True)` or by holding masked data) | `Bool` (`tableIsMasked`) | `True ↔ true`. Governs the `self.ColumnClass` / `_get_col_cls_for_table` sinks; the `masked_col_cls` sink is `MaskedColumn` regardless. |
| `col_cls` finally chosen / early mixin return | `ColumnKind` (inductive) | non-masked `Column` family (`self.ColumnClass` when table unmasked / `_get_col_cls_for_table` non-upgrading) ↔ `.columnKind`; `MaskedColumn` (`masked_col_cls`, or `self.ColumnClass`/`_get_col_cls_for_table` when the table is masked) ↔ `.maskedColumnKind`; an early-returned mixin column (e.g. `NdarrayMixin`) ↔ `.mixinKind`. The F2P tests observe `isinstance(t['a'], Column)` / `MaskedColumn` / `NdarrayMixin`, i.e. exactly this kind. |

`Column`/`MaskedColumn`/`NdarrayMixin` are the three column-class kinds the F2P
tests discriminate via `isinstance` (`test_ndarray_mixin[False]` asserts a
structured array becomes a `Column`; `test_structured_masked_column` asserts a
masked structured array becomes a `MaskedColumn` and preserves its mask). The
abstraction keeps only the class-kind the tests observe, not the column's data.

Empirical cross-check (astropy 5.2.2, post-patch): adding each of the six
input shapes to an unmasked and to a masked `Table` and reading back
`type(t['a'])` reproduces exactly `classify` on all 12 cells —
unmasked table: Column, NdarrayMixin, Column, MaskedColumn, MaskedColumn,
Column; masked table: MaskedColumn, NdarrayMixin, MaskedColumn, MaskedColumn,
MaskedColumn, MaskedColumn.

## 3. Callee provenance (no axioms)

None. The classification is a pure dispatch over the input's shape and the
table's masked-ness flag, modeled **deeply** as `classify`. The callees the
surrounding code invokes (`_is_mixin_for_table`, `_get_col_cls_for_table`,
`col_copy`, `view`) are NOT axiomatized: their relevant effect is already
collapsed into the `InputShape`/`tableIsMasked` inputs and the `ColumnKind`
result (mapping.md §2). There is therefore no A-consumed axiom and no
A-reference deep model of an outside callee — `meta.json axioms = []`,
`deep_model_references = []`.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **13236**. The R/I shadow
is the modeled dispatch `classify` transliterated to Python; the oracle is the
**patched** selection logic, transliterated verbatim from the post-image of
`_convert_data_to_col` (see `conformance_check.py` docstring for why the real
`_convert_data_to_col` is not driven end-to-end in-container — it requires a
fully built `Table` context and numpy class machinery merely to read back one
class kind; the transliteration is instead empirically cross-checked against
astropy 5.2.2, §2 above). Both are exercised over the full finite input space
(every `InputShape` × `tableIsMasked`) plus seeded fuzz.
