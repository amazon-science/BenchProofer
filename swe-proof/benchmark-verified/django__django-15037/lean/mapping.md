# mapping.md — symbol binding & type bijection (django__django-15037)

## Modeled function
- **Lean** `implementation_relationField : Bool → Bool → String → String → String → Option String → RelationField`
- **Python** the relation-column block of `Command.handle_inspection`'s inner
  per-column loop — `django/core/management/commands/inspectdb.py:116-133 @ dab48b7`
  (the `if is_relation:` branch that computes `rel_type`, `rel_to`, and the new
  `extra_params['to_field']`).

The function under spec is the post-patch `is_relation` branch. The patch adds,
inside the plain foreign-key sub-branch, a lookup of the referenced table's
primary-key column and, when that column exists and differs from the referenced
column, records the referenced column as an explicit target column
(`extra_params['to_field']`). The `rel_to` computation is refactored to reuse
the unpacked `(ref_db_column, ref_db_table) = relations[column_name]` but is
behaviourally identical.

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| `extra_params.pop('unique', False)` (a bool) | `isUnique : Bool` | whether the column carries a unique constraint at this point |
| `extra_params.get('primary_key')` (truthy) | `isPrimaryKey : Bool` | whether the column is the table's primary key |
| `ref_db_column` (= `relations[column_name][0]`, a `str`) | `refDbColumn : String` | the referenced column name |
| `ref_db_table` (= `relations[column_name][1]`, a `str`) | `refDbTable : String` | the referenced table name |
| `table_name` (a `str`) | `tableName : String` | the current table being introspected |
| `ref_pk_column` (a `str` or falsy: `None`/`''`) | `refPkColumn : Option String` | `get_primary_key_column(cursor, ref_db_table)`; Python truthiness `None`/`''` → `none`, a non-empty name → `some name` |
| `rel_type` (`'ForeignKey'`/`'OneToOneField'`) | `result.relType : String` | field kind literal |
| `rel_to` (`'self'` or `table2model(ref_db_table)`) | `result.relTo : String` | referenced target |
| `extra_params.get('to_field')` (`str` or absent) | `result.toField : Option String` | explicit target column; absent → `none` |
| `table2model(name)` | `dbTableToModelName name` | opaque deterministic table-name → model-id transform |

### Python-truthiness modeling note
The patch guards on `if ref_pk_column and ref_pk_column != ref_db_column`. Python
treats `None` and `''` (an empty primary-key column name — the introspection
returns `None` when no pk is detectable) as falsy. The `Option String` model
collapses both falsy cases to `none`; a real non-empty pk column name maps to
`some`. The second conjunct `ref_pk_column != ref_db_column` is `pk ≠ refDbColumn`.

## Callee provenance
- **`table2model`** (`inspectdb.py:43`, the inner `table2model(table_name)` =
  `re.sub(r'[^a-zA-Z0-9]', '', table_name.title())`) is an UNCHANGED callee the
  fix uses to build `rel_to`. It is declared `opaque dbTableToModelName : String
  → String` so it appears in the executable impl. The proof relies ONLY on its
  being a function (the spec mirrors the impl's call site), so NO `_prop` axiom
  is consumed — it is validated as an **A-reference** by G-AX against the real
  `table2model`.
- **`connection.introspection.get_primary_key_column(cursor, ref_db_table)`**
  (the changed op's new callee) is NOT modeled as a Lean computation: its result
  is an INPUT to the modeled function (`refPkColumn : Option String`). It is a DB
  introspection side-effect, not a pure transform; lifting its result to an input
  is the faithful frame (G-CONF feeds the same value to both legs). No axiom.

## Flag dependency
None. The branch behaviour depends only on the `isUnique`/`isPrimaryKey` booleans
and the referenced-table/column/pk inputs.

## G-CONF fuzz seed
Pinned seed: **15037**. ≥10^5 fuzzed inputs over an alphabet of plausible
column/table names (including equal/unequal pk-vs-column and self/non-self
cases, and `none` pk), with the unique/primary-key booleans fuzzed.
