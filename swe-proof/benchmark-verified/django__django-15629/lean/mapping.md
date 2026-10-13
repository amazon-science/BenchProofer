# mapping.md — django__django-15629

Symbol binding, type bijection, callee provenance, and the pinned G-CONF fuzz
seed. All file:line references are at `base_commit`
`694cf458f16b8d340a3195244196980b2dec34fd`.

## Modeled behaviors (three independently-observable decisions)

The issue: a primary-key column's collation is not carried over to the columns
of related fields that point at it, so the generated `ALTER TABLE … ADD
CONSTRAINT` for the foreign key fails (the referencing column's collation does
not match the referenced column's). The gold fix has three observable parts.

### A. Related-field parameter mapping carries the referenced column's collation
- Python: `ForeignKey.db_parameters(self, connection)` —
  `django/db/models/fields/related.py:1182-1183` @ base_commit.
  Pre-patch returns `{"type": …, "check": …}`. Post-patch also returns
  `"collation": target_db_parameters.get("collation")`, where
  `target_db_parameters = self.target_field.db_parameters(connection)`.
- Lean: `implementation_fkColumnParams` / `problem_spec_fkColumnParams` /
  `correct_fkColumnParams`.

### B. The "rebuild incoming references" decision also fires on a collation change
- Python: the `drop_foreign_keys` predicate inside
  `BaseDatabaseSchemaEditor._alter_field` —
  `django/db/backends/base/schema.py:826-833` @ base_commit. Pre-patch's last
  conjunct is `old_type != new_type`; post-patch is
  `(old_type != new_type) or (old_collation != new_collation)`. (The sqlite3
  backend `SQLiteSchemaEditor._alter_field`,
  `django/db/backends/sqlite3/schema.py:458`, makes the same collation-aware
  widening for its `new_field.unique and …` guard — same decision.)
- Lean: `implementation_rebuildIncomingFks` / `problem_spec_rebuildIncomingFks`
  / `correct_rebuildIncomingFks`.

### C. Re-altering a referencing column uses the collation branch when the collation changed
- Python: the `for old_rel, new_rel in rels_to_update` loop inside
  `BaseDatabaseSchemaEditor._alter_field` —
  `django/db/backends/base/schema.py:1038-1043` @ base_commit. Pre-patch always
  calls `_alter_column_type_sql`. Post-patch first computes
  `rel_collation` / `old_rel_collation` and, when they differ, calls
  `_alter_column_collation_sql` (with `other_actions = []`) instead.
- Lean: `implementation_relatedColumnAlterKind` /
  `problem_spec_relatedColumnAlterKind` / `correct_relatedColumnAlterKind`.

## Type bijection (Lean ↔ Python) — used by G-CONF and G-AX

| Python | Lean |
|---|---|
| `db_parameters` dict `{"type": str, "check": str|None, "collation": str|None}` | `structure ColumnParams` with `colType : String`, `checkExpr : Option String`, `collation : Option String` |
| `self.db_type(connection)` (a `str`) | `fkType : String` (input) |
| `self.db_check(connection)` (`None` for FK) | `fkCheck : Option String` (input) |
| `self.target_field.db_parameters(connection)` | `targetParams : ColumnParams` (input) |
| `dict.get("collation")` → `str | None` | `.collation : Option String` |
| `supports_foreign_keys`, `*.primary_key`, `*.unique` (bool) | `Bool` inputs |
| `old_type`, `new_type` (`str`) | `String` inputs |
| `old_collation`, `new_collation`, `rel_collation`, `old_rel_collation` (`str | None`) | `Option String` inputs |
| Python `!=` on strings / `str|None` | Lean `!=` (`BEq` on `String` / `Option String`) |
| which-SQL-branch is taken (`_alter_column_collation_sql` vs `_alter_column_type_sql`) | `inductive RelAlterKind` = `collationAlter | typeAlter` |

`None` ↔ `Option.none`; a present collation string `s` ↔ `Option.some s`.

## Callee provenance / flag deps

- `target_field.db_parameters(connection)` is treated as an INPUT
  (`targetParams`) — the referenced column's already-computed parameter mapping,
  not a callee modeled inside the triple. Its `.collation` value is grounded
  data (directive 8): the spec reads it from the input carrier.
- `_alter_column_collation_sql` / `_alter_column_type_sql` are NOT modeled
  internally; only the *choice between them* (decision C) is modeled, as the
  `RelAlterKind` sum. No `opaque` callee, no consumed axiom, no A-reference deep
  model is needed.
- No flag-dependent callee (no `quote=`-style configuration to fuzz).

## G-CONF / G-AX

- No consumed axiom and no A-reference deep model → `axiom_check.py` is a skip
  stub (`status=skip`).
- The impl region is all R/I → `conf_skip=false`; `conformance_check.py` runs a
  real fuzz over all three decisions.
- **Pinned G-CONF fuzz seed: 15629.**
