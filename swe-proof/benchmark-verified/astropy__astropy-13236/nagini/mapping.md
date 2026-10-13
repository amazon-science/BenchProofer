# mapping.md — astropy__astropy-13236

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 6ed769d58d89380ebaa1ef52b300691eefda8928`, states the type
abstraction, and gives the provenance of each axiomatised/unchanged callee.

Repo file under change: `astropy/table/table.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `select_column_kind(...)` | `Table._convert_data_to_col(self, data, ...)` — `astropy/table/table.py:1179` (the class-selection if/elif chain, body lines 1242-1313) | the modeled changed method: which column-class the input data is converted to |
| `KIND_MIXIN` (= 0) | the early `return col` mixin branch — `table.py:1268-1273` (`elif data_is_mixin:` → `col_copy(...)`/`data`, returns a mixin-class object as-is) | result code: input handed back as its mixin class |
| `KIND_SEQ_MIXIN` (= 1) | the sequence-of-mixin branch — `table.py:1275-1280` (`elif data0_is_mixin:` → `data[0].__class__(data)`) | result code: a sequence of mixins, built as the element mixin class |
| `KIND_MASKED` (= 2) | the masked branch — `table.py:1286-1290` (`elif isinstance(data, (np.ma.MaskedArray, Masked))` → `col_cls = masked_col_cls`) → a `MaskedColumn`; **and** the `isinstance(data, Column)` upgrade branch (`table.py:1259-1266`) when the input column is itself masked | result code: MaskedColumn |
| `KIND_COLUMN` (= 3) | the plain branch — `table.py:1312-1313` (`else: col_cls = self.ColumnClass`) and the `isinstance(data, Column)` upgrade branch (`table.py:1259-1266`) when the input column is NOT masked and the None branch and the no-dtype branch when its converted sequence carries no mask; all build a `Column`/`ColumnClass` | result code: a (non-masked) Column |

The `isinstance(data, Column)` upgrade branch (`table.py:1259-1266`) is the FIRST
guard of the chain and it is not uniformly `KIND_COLUMN`. `_get_col_cls_for_table`
returns `col.__class__` for a table whose own `ColumnClass` is not a masked one,
so an input that is already a column keeps its own column nature: a `MaskedColumn`
(which is both a `Column` and a `np.ma.MaskedArray`) stays a `MaskedColumn`, i.e.
`KIND_MASKED`, while a plain `Column` stays `KIND_COLUMN`. The model carries this
as the leading `is_column` arm of `selected_kind`, split on `is_masked`. Reading
this branch as uniformly `KIND_COLUMN` mis-values every already-masked-column
input; reading the branch taken from the STORED CLASS alone cannot distinguish it
from the masked branch (both yield `MaskedColumn` on a default `Table`), so
`conformance_check.py` traces the branch line itself.

Note the no-dtype branch (`table.py:1300-1310`, `elif not hasattr(data, 'dtype'):`)
is NOT uniformly `KIND_COLUMN`: it converts the sequence and picks the masked
column class when the conversion yields a masked array (a list with embedded
masked entries). The model carries this as the `seq_masked` bit (§2), so the
kind on that branch is `KIND_MASKED` iff `seq_masked` else `KIND_COLUMN`.

The pre-patch repo lines the change *removes* (relevant to the refinement
audit, not referenced from the consumer spec view): `table.py:1242-1247`, the
clause

```
if (not isinstance(data, Column) and not data_is_mixin
        and isinstance(data, np.ndarray) and len(data.dtype) > 1):
    data = data.view(NdarrayMixin)
    data_is_mixin = True
```

which, when its guard holds, reassigns `data` to a mixin view and sets
`data_is_mixin = True`, thereby diverting an input that would otherwise be
classified by the masked / plain branches into the `KIND_MIXIN` early-return
branch.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `isinstance(data, Column)` | `bool` `is_column` | the runtime instance test, evaluated by the caller of the model; carries one bit |
| `data_is_mixin` (`Table._is_mixin_for_table(data)`, possibly updated by `get_mixin_handler`) | `bool` `is_mixin` | the mixin classification bit as it stands *before* the removed clause (the handler block at lines 1232-1240 runs first and is unchanged by the patch) |
| `data0_is_mixin` (`Table._is_mixin_for_table(data[0])`) | `bool` `data0_is_mixin` | the "first element is a mixin" bit |
| `isinstance(data, np.ndarray)` | `bool` `is_ndarray` | one bit; a `np.ma.MaskedArray` IS an `np.ndarray`, so this bit is also true for masked arrays (load-bearing for `test_structured_masked_column`) |
| `len(data.dtype) > 1` | `bool` `is_structured` | one bit: the dtype is a structured (record) dtype with more than one field |
| `isinstance(data, (np.ma.MaskedArray, Masked))` | `bool` `is_masked` | one bit |
| `data is None` | `bool` `is_none` | one bit |
| `hasattr(data, 'dtype')` | `bool` `has_dtype` | one bit (an `np.ndarray` always has a dtype, so `is_ndarray ⇒ has_dtype`) |
| `isinstance(_convert_sequence_data_to_array(data, dtype), np.ma.MaskedArray)` — evaluated only on the `elif not hasattr(data, 'dtype'):` branch (`table.py:1300-1310`) | `bool` `seq_masked` | one bit: a dtype-less input (e.g. a plain list) whose sequence-to-array conversion yields a masked array (it contains masked entries). Defined only when `not has_dtype` (encoded `seq_masked ⇒ not has_dtype`); on that branch the real code picks `masked_col_cls` iff this bit is true, so the stored kind is `KIND_MASKED` iff it is true. |
| the selected `col_cls` / early mixin return | `int` result code (0..3, see §1) | the test-observable distinction is which column *kind* results (`isinstance(t['a'], Column)` vs `NdarrayMixin` vs `MaskedColumn`); the exact subclass upgrade (`_get_col_cls_for_table`) is unchanged by the patch and not part of the modeled delta |

No `str`/`float` is involved; the modeled delta is a pure boolean decision
procedure, so the carrier is `bool`/`int` and no `--float-encoding` flag is
needed.

## 3. Callee provenance (unchanged callees — NOT axiomatised inside Ensures)

The if/elif chain itself is the changed code. The booleans it branches on are
produced by unchanged callees / Python `isinstance`:

- `Table._is_mixin_for_table` (`table.py:1218`, and re-evaluated inside the
  unchanged handler block at 1235) — classifies whether an object is a mixin
  column for this table. Unchanged by the patch. In the model its result is an
  abstract input bit `is_mixin` (and `data0_is_mixin`); the model does not
  re-derive it, so there is **no `@ContractOnly` axiom** about it — it is an
  R-refinement of a runtime predicate into a boolean input.
- `isinstance(...)` / `hasattr(...)` / `len(dtype)` — Python built-ins; their
  results are abstract input bits (`is_column`, `is_ndarray`, `is_structured`,
  `is_masked`, `is_none`, `has_dtype`). R-refinements, not axioms.
- `col_copy`, `col_cls(...)` construction, `_get_col_cls_for_table`,
  `_convert_col_for_table`, `_convert_sequence_data_to_array`,
  `get_mixin_handler` — callees on the branch *bodies*. The patch does not
  change any of them, and the test-observable delta is only *which branch is
  taken* (which column kind). The model abstracts each branch body to its
  result kind code; the bodies are unchanged identical operations (tag I in
  refinement.md), not axioms consumed inside an `Ensures`.

Because the modeled delta is a control-flow decision over abstract boolean
classification bits, there is **no `@ContractOnly` axiom and no deep-model
A-reference**: nothing stdlib/opaque is consumed inside an `Ensures`. The
`axioms` region is therefore empty. (`axiom_check.py` instead validates that the
real `_convert_data_to_col` produces the model's decision on the F2P inputs and
on a structured-ndarray fuzz of the classification bits — see §4 there.)

## 4. Constraints among the input bits (domain facts, encoded as Requires)

Real `np` semantics impose relations the model encodes as preconditions so that
the decision procedure is only specified on realisable inputs:

- `is_masked ⇒ is_ndarray` (a `np.ma.MaskedArray` is an `np.ndarray`).
- `is_ndarray ⇒ has_dtype` (an ndarray always has a `dtype`).
- `is_masked ⇒ not is_none` and `is_ndarray ⇒ not is_none` (None is not an
  array).
- `seq_masked ⇒ not has_dtype` (the sequence-conversion probe is evaluated
  only on the no-dtype branch; an object that already has a `dtype` never
  takes that path, so the bit is defined false there).
- `elem_cls_builds ⇒ (data0_is_mixin and not is_column)` (the element-class
  construction probe is the `try` inside the sequence-of-mixins branch,
  `table.py:1277-1280`; it is only reached for a non-column input whose first
  element is a mixin, so the bit is defined false elsewhere).
- `is_column ⇒ not is_mixin` — `Table._is_mixin_for_table`
  (`astropy/table/table.py:1580`) returns `False` immediately for any
  `BaseColumn`, so no column object is ever classified as a mixin.
- `is_column ⇒ has_dtype` — `Column`/`MaskedColumn` are `np.ndarray`
  subclasses, so a column object always carries a `dtype`.
- `is_column ⇒ not is_none` — a column object is not the `None` object.

These are the only facts the proof relies on; they are exactly what
`axiom_check.py` respects when it constructs real inputs, and
`conformance_check.py` re-derives every one of them from the real classes it
generates rather than assuming them.

Alongside them the precondition carries `MustTerminate(1)`, which is NOT a
constraint on the inputs: it narrows nothing, it obliges the implementation to
reach a decision on every input already in the domain. The real
`Table._convert_data_to_col` (`astropy/table/table.py:1179`) is a straight-line
`if`/`elif` chain over `isinstance`/`hasattr` probes with no loop and no
recursion on any of these paths, so it terminates on every admissible input and
the obligation is TRUE of it, both before and after the gold patch (the patch
only deletes a clause — it removes code, so it cannot introduce divergence).
Without the obligation Nagini proves only PARTIAL correctness: every value
clause is claimed of runs that reach the `return`, so an implementation that
never returns on the structured-array family satisfies them vacuously there and
verifies. That was a measured hole in this cell (`properties.py` reject case
`weak-nonterminating-on-structured`), which is why the obligation is stated. It
costs the gold-faithful model nothing (`model.py` still verifies) and does not
rescue the prepatch twin, whose divergence is a wrong VALUE, not a hang.
