# refinement.md — operation correspondence (django__django-15037)

Maps every op in `implementation_relationField` to its `patch.diff` counterpart.
Tags: **R** type refinement · **A-consumed** proof uses axiom property ·
**A-reference** deep model validated == real callee (G-AX) · **I** identical op.

Post-patch Python (the `if is_relation:` branch, `inspectdb.py:118-133`):
```python
ref_db_column, ref_db_table = relations[column_name]
if extra_params.pop('unique', False) or extra_params.get('primary_key'):
    rel_type = 'OneToOneField'
else:
    rel_type = 'ForeignKey'
    ref_pk_column = connection.introspection.get_primary_key_column(cursor, ref_db_table)
    if ref_pk_column and ref_pk_column != ref_db_column:
        extra_params['to_field'] = ref_db_column
rel_to = (
    'self' if ref_db_table == table_name
    else table2model(ref_db_table)
)
```

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `(ref_db_column, ref_db_table) = relations[column_name]` → `refDbColumn refDbTable` inputs | `ref_db_column, ref_db_table = relations[column_name]` | R | `str × str` ↔ two `String` inputs (mapping.md); destructure of the relations entry, lifted to inputs |
| 2 | `if isUnique || isPrimaryKey then relType := "OneToOneField"` | `if extra_params.pop('unique', False) or extra_params.get('primary_key'): rel_type = 'OneToOneField'` | R | Python bool/truthy ↔ `Bool` (mapping.md); identical disjunction |
| 3 | `else relType := "ForeignKey"` | `else: rel_type = 'ForeignKey'` | I | identical literal assignment |
| 4 | `match refPkColumn with \| some pk => if pk ≠ refDbColumn then toField := some refDbColumn \| none => pure ()` | `ref_pk_column = ...get_primary_key_column(...); if ref_pk_column and ref_pk_column != ref_db_column: extra_params['to_field'] = ref_db_column` | R | `get_primary_key_column`'s result is the input `refPkColumn : Option String` (mapping.md truthiness note); the `ref_pk_column and ...` falsy guard ↔ the `some/none` match; `!=` ↔ `≠`. The introspection callee is NOT axiomatized — its observable output is the modeled function's input. |
| 5 | `let relTo := if refDbTable = tableName then "self" else dbTableToModelName refDbTable` | `rel_to = ('self' if ref_db_table == table_name else table2model(ref_db_table))` | A-reference | `table2model` is the UNCHANGED callee, declared `opaque dbTableToModelName`, validated == real `table2model` by G-AX. String `==` ↔ Lean `=`. |
| 6 | `return { relType, relTo, toField }` | the three values fed into the downstream `field_type`/`extra_params` formatting | I | structure pack of the three computed outputs |

No A-consumed rows: the proof discharges the spec by `rfl`/case analysis on the
impl's control flow; no UNCHANGED-callee *property* is assumed (the only opaque,
`dbTableToModelName`, appears identically in spec and impl, so equality holds
definitionally). No changed-inexpressible op.

## Discriminating clause (G-DIFF)
Row 4 — `toField`. The pre-patch code computed neither `ref_pk_column` nor
`to_field`, so `extra_params` never gained a `to_field` entry: the prepatch impl
leaves `toField = none` unconditionally. Against the frozen
`problem_spec_relationField` (which requires `toField = some refDbColumn` exactly
when the field is a plain foreign key and the referenced table has a detected pk
column differing from the referenced column), `correct_relationField` cannot
close — the `.toField` conjunct fails to typecheck by `rfl`. That is the G-DIFF
signal and matches the F2P test `test_foreign_key_to_field`.
