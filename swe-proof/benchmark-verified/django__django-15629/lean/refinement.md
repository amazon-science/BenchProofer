# refinement.md — django__django-15629

Every operation in each `implementation_<name>` mapped to its `patch.diff`
counterpart. Tags: **R** (type-only refinement), **A-consumed** (proof uses an
axiom's property), **A-reference** (deep model validated == real callee by
G-AX), **I** (identical concrete op). Three modeled decisions; no A-tagged ops.

## Triple 1 — `implementation_fkColumnParams` ↔ `ForeignKey.db_parameters`
`django/db/models/fields/related.py:1182-1183` @ base_commit (post-patch hunk).

| # | Lean op | patch.diff op | tag |
|---|---|---|---|
| 1 | init `params := { colType := fkType, checkExpr := fkCheck, collation := none }` | post-patch dict `{"type": self.db_type(connection), "check": self.db_check(connection), "collation": …}` keys `type`/`check` | R (dict → `ColumnParams`; `str`↔`String`, `str|None`↔`Option String`) |
| 2 | `params := { params with collation := targetParams.collation }` | `"collation": target_db_parameters.get("collation")` where `target_db_parameters = self.target_field.db_parameters(connection)` | R (`target_field.db_parameters` taken as INPUT `targetParams`; `.get("collation")` ↔ `.collation`) |
| 3 | `return params` | `return {…}` | I |

## Triple 2 — `implementation_rebuildIncomingFks` ↔ `drop_foreign_keys` predicate
`django/db/backends/base/schema.py:826-833` @ base_commit (post-patch). Same
collation-aware widening appears in `sqlite3/schema.py:455-462` guard.

| # | Lean op | patch.diff op | tag |
|---|---|---|---|
| 1 | `decision := supportsFk` | `self.connection.features.supports_foreign_keys` | R (attr → `Bool`) |
| 2 | `decision := decision && ((oldPk && newPk) || (oldUnique && newUnique))` | `and ((old_field.primary_key and new_field.primary_key) or (old_field.unique and new_field.unique))` | R (`and`/`or` ↔ `&&`/`||`) |
| 3 | `decision := decision && ((oldType != newType) || (oldCollation != newCollation))` | `and ((old_type != new_type) or (old_collation != new_collation))` — the changed conjunct | R/I (the fix: collation disjunct added; `!=` ↔ `!=`) |
| 4 | `return decision` | value of `drop_foreign_keys` | I |

## Triple 3 — `implementation_relatedColumnAlterKind` ↔ rels-to-update branch
`django/db/backends/base/schema.py:1038-1043` @ base_commit (post-patch).

| # | Lean op | patch.diff op | tag |
|---|---|---|---|
| 1 | `if oldRelCollation != relCollation then return RelAlterKind.collationAlter` | post-patch `if old_rel_collation != rel_collation: fragment = self._alter_column_collation_sql(…); other_actions = []` | R (which-branch-taken ↔ `RelAlterKind`; the called SQL helper is abstracted to the choice, not modeled) |
| 2 | `return RelAlterKind.typeAlter` | `else: fragment, other_actions = self._alter_column_type_sql(…)` | R (same) |

`old_rel_collation`/`rel_collation` are derived from
`old_rel.field.db_parameters(...).get("collation")` and
`new_rel.field.db_parameters(...).get("collation")` respectively; taken as the
two `Option String` inputs (decision C is the branch selection only).

## No changed-inexpressible op
Every changed op is modeled directly (R/I). No callee axiom is consumed and no
deep-model reference exists, so `axiom_check.py` is a skip stub and
`conf_skip=false` (G-CONF runs a real fuzz over all three decisions).
