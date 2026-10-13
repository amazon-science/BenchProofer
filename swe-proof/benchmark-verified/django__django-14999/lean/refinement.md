# refinement.md — operation correspondence (django__django-14999)

Maps every op in `implementation_renameModel` to its `patch.diff` counterpart.
Tags: **R** type refinement · **A-consumed** proof uses axiom property ·
**A-reference** deep model validated == real callee (G-AX) · **I** identical op.

The patched Python (`RenameModel.database_forwards`):
```python
if self.allow_migrate_model(schema_editor.connection.alias, new_model):
    old_model = from_state.apps.get_model(app_label, self.old_name)
    old_db_table = old_model._meta.db_table
    new_db_table = new_model._meta.db_table
    # Don't alter when a table name is not changed.
    if old_db_table == new_db_table:
        return
    schema_editor.alter_db_table(new_model, old_db_table, new_db_table)
    # ... dependent related-objects loop + m2m loop (UNCHANGED) ...
```
We model the function's *result* as the ordered list of emitted schema
operations (`List SchemaOp`) — the observable signal the F2P test measures via
`assertNumQueries(0)` (see mapping.md).

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `if !allowMigrate then return []` | `if self.allow_migrate_model(...):` (else: skip body) | R | Bool guard ↔ truthiness of `allow_migrate_model`; emitting nothing ↔ skipping the body. UNCHANGED pre-existing control flow. |
| 2 | `if oldDbTable == newDbTable then return []` | `if old_db_table == new_db_table: return` | I | the ADDED guard — str equality of the stored table names; early return ⇒ no operations emitted. This is the fix. |
| 3 | `acc := acc ++ [SchemaOp.renameTable oldDbTable newDbTable]` | `schema_editor.alter_db_table(new_model, old_db_table, new_db_table)` | R | the main table rename is reified as one `renameTable old new` datum (mapping.md bijection). Carries the same two table-name arguments. |
| 4 | `acc := acc ++ tailOps` | dependent related-objects loop + m2m loop (`alter_field` / `alter_db_table` calls) | R | the UNCHANGED follow-up operations, abstracted as the opaque input list `tailOps` and passed through in order (tail abstraction, mapping.md). No changed op hidden here. |
| 5 | `return acc` | (fall-through end of method) | I | returns the accumulated operation sequence. |

No A-consumed rows and no A-reference rows: the impl is self-contained
structural control flow over reified `SchemaOp` data; no UNCHANGED callee
property is assumed and no deep model of a real callee's internals is made.
Hence the `axioms` region is empty and `axiom_check.py` is a skip stub.

The discriminating clause is row 2 (the added guard), captured by the spec's
middle conjunct `allowMigrate = true → oldDbTable = newDbTable → result = []`.
The prepatch impl omits the guard, so when `oldDbTable = newDbTable` it yields
`SchemaOp.renameTable … :: tailOps ≠ []`; its `correct_renameModel` cannot close
that conjunct against the frozen `problem_spec_renameModel`. That is the G-DIFF
signal. `database_backwards` only swaps names and re-invokes `database_forwards`,
so it inherits the same fix — one prepatch variant suffices.
