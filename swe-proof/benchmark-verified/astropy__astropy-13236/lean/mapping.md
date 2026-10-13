# mapping.md — astropy__astropy-13236

## Symbol binding (file:line @ base_commit 6ed769d58d89380ebaa1ef52b300691eefda8928)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_columnForTableData` / `problem_spec_columnForTableData` | `Table._convert_data_to_col` (the column-class selection it performs) | `astropy/table/table.py:1179-1320` |
| `ConvInput` (pure helper) | the observations of `data` after handler resolution that the class decision depends on | the locals `data`, `data_is_mixin`, `data0_is_mixin` and their `isinstance`/`dtype` probes | `table.py:1217-1320` |
| `ColClass` (pure helper) | the *class* of the column object the function ultimately produces | `Column` / `MaskedColumn` / `NdarrayMixin` / any pre-existing mixin class |
| `convResultClass` (pure helper) | the body computing `col_cls` / the early mixin-`return` | `table.py:1247-1313` |

The modeled function is the column-class **selection** inside
`Table._convert_data_to_col`. It is the only behavior the patch changes and the
only behavior the FAIL_TO_PASS tests observe:

- `test_mixin.py::test_ndarray_mixin[False]` adds plain (non-`Column`,
  non-mixin) **structured** `ndarray`s `a`, `b`, `c` to a `Table()` and asserts
  each resulting column is a `Column` (was `NdarrayMixin`).
- `test_table.py::test_structured_masked_column` adds a **masked** structured
  `ndarray` and asserts the resulting column is a `MaskedColumn` (was
  `NdarrayMixin`).

### What the function does (base_commit)

After resolving any mixin *handler*, `_convert_data_to_col` decides the column
class as follows (base_commit):

```python
# Structured ndarray gets viewed as a mixin unless already a valid mixin class
if (not isinstance(data, Column) and not data_is_mixin
        and isinstance(data, np.ndarray) and len(data.dtype) > 1):
    data = data.view(NdarrayMixin)        # <-- the removed clause
    data_is_mixin = True
# ... name determination (no effect on class) ...
if isinstance(data, Column):
    col_cls = self._get_col_cls_for_table(data)
elif data_is_mixin:
    col = col_copy(data, ...) if copy else data
    col.info.name = name
    return col                            # returned as-is, class preserved
elif data0_is_mixin:
    try: col = data[0].__class__(data); col.info.name = name; return col
    except Exception: data = np.array(data, dtype=object); col_cls = self.ColumnClass
elif isinstance(data, (np.ma.MaskedArray, Masked)):
    col_cls = masked_col_cls              # MaskedColumn
elif data is None:
    data = np.array(None); col_cls = self.ColumnClass
elif not hasattr(data, 'dtype'):
    data = _convert_sequence_data_to_array(data, dtype)
    col_cls = masked_col_cls if isinstance(data, np.ma.MaskedArray) else self.ColumnClass
else:
    col_cls = self.ColumnClass            # Column
col = col_cls(name=name, data=data, ...)
```

`len(data.dtype)` is `0` for an unstructured dtype and the number of fields for a
structured dtype; `len(data.dtype) > 1` therefore selects multi-field
(structured) arrays. The removed clause forces such arrays (when not already a
`Column`/mixin) to `NdarrayMixin` and then returns them via the `data_is_mixin`
branch. With the clause gone, a plain structured `ndarray` reaches the final
`else` (→ `self.ColumnClass`, i.e. `Column`) and a masked structured array
reaches the `np.ma.MaskedArray` branch (→ `masked_col_cls`, i.e. `MaskedColumn`).

### Lean modeling

- `ConvInput` records the observable booleans/counts the decision reads, *after*
  the unchanged mixin-handler step (which is upstream of the touched region):
  `isColumn` (`isinstance(data, Column)`), `isMixin` (`data_is_mixin`),
  `data0IsMixin` (`data0_is_mixin`), `isNdarray` (`isinstance(data, np.ndarray)`,
  true for masked arrays too), `numDtypeFields` (`len(data.dtype)`),
  `isMaskedArray` (`isinstance(data, (np.ma.MaskedArray, Masked))`), `isNone`
  (`data is None`), `hasDtype` (`hasattr(data, 'dtype')`).
- The *results* of the three unchanged sub-decisions are carried as grounded
  observations rather than re-modeled (they are upstream/orthogonal to the fix):
  `columnInputResult` = `self._get_col_cls_for_table(data)` for an existing
  `Column`; `dataMixinClass` = the class of a pre-existing mixin returned as-is;
  `seqMixinResult` = the class produced by the sequence-of-mixin branch (incl.
  its object-array fallthrough); `seqConvMasked` = whether
  `_convert_sequence_data_to_array` yields a `MaskedArray` in the no-`dtype`
  branch.
- Table-level class parameters: `tableColumnClass` = `self.ColumnClass`,
  `tableMaskedColumn` = `masked_col_cls`. For the F2P scenario (a plain
  `Table()`), `tableColumnClass = Column` and `tableMaskedColumn = MaskedColumn`.
- The post-patch decision is `convResultClass`; the impl is the
  `Id.run do` skeleton mirroring the if/elif chain (the removed clause absent).
  The pre-patch impl re-introduces the clause as a leading early-`return
  ColClass.ndarrayMixin` (behaviourally identical to viewing-as-mixin then
  returning via the `data_is_mixin` branch).

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | bijection |
|---|---|---|
| the produced column object's class | `ColClass` | `Column ↔ .column`, `MaskedColumn ↔ .maskedColumn`, `NdarrayMixin ↔ .ndarrayMixin`, any other mixin class ↔ `.otherMixin` |
| `isinstance(data, Column)` | `isColumn : Bool` | identity |
| `data_is_mixin` (`_is_mixin_for_table(data)`) | `isMixin : Bool` | identity |
| `data0_is_mixin` | `data0IsMixin : Bool` | identity |
| `isinstance(data, np.ndarray)` | `isNdarray : Bool` | identity (masked arrays included) |
| `len(data.dtype)` | `numDtypeFields : Nat` | `0` if unstructured; field count if structured |
| `isinstance(data, (np.ma.MaskedArray, Masked))` | `isMaskedArray : Bool` | identity |
| `data is None` | `isNone : Bool` | identity |
| `hasattr(data, 'dtype')` | `hasDtype : Bool` | identity |
| `self.ColumnClass` | `tableColumnClass : ColClass` | the table's default column class |
| `masked_col_cls` | `tableMaskedColumn : ColClass` | the table's masked column class |

The function's observable result is the class of the returned column; we model it
as `result : ColClass`.

## Callee provenance + flag dependencies

- **No consumed callee axiom.** The behavior the patch changes — the column class
  chosen for a structured `ndarray` — is modeled DEEPLY and structurally over the
  observable flags (`isColumn`, `isMixin`, `isNdarray`, `numDtypeFields`,
  `isMaskedArray`); SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled changed
  decision. So the `axioms` region is empty and **G-AX skips**.
- `get_mixin_handler` / `handler(data)` and `_is_mixin_for_table` run upstream of
  the touched region; their net effect is folded into `isMixin` (and the possibly
  rebound `data`). Unchanged by the patch; not separately modeled.
- `_get_col_cls_for_table` (the existing-`Column` upgrade), the sequence-of-mixin
  construction `data[0].__class__(data)`, and `_convert_sequence_data_to_array`
  (the no-`dtype` branch) are all UNCHANGED by the patch and orthogonal to the
  structured-array fix; their results are carried as grounded observations
  (`columnInputResult`, `seqMixinResult`, `seqConvMasked`). They constrain no
  output component the spec leaves free — the spec pins the full result class.

## G-CONF fuzz seed

Pinned LCG seed: **13236** (see `conformance_check.py` `SEED`). Corpus: randomized
`ConvInput`s crossing every branch flag, with emphasis on the discriminating
category — structured `ndarray`s (`isNdarray=True`, `numDtypeFields ∈ {2,3,4}`,
`isColumn=isMixin=False`), masked and unmasked — plus control inputs hitting the
`Column`, mixin, sequence-of-mixin, `None`, and no-`dtype` branches, over ≥1e5
fuzzed inputs. The R/I shadow of `implementation_columnForTableData` is diffed
against an in-process replica of the POST-PATCH selection. Hand-picked edge cases
pin the discriminating clause: an unmasked structured `ndarray` → `Column` and a
masked structured `ndarray` → `MaskedColumn`.
