# mapping.md — symbol binding & type bijection (django__django-14999)

## Modeled function
- **Python:** `RenameModel.database_forwards(self, app_label, schema_editor, from_state, to_state)`
  in `django/db/migrations/operations/models.py`, lines **319–368 @ base_commit
  `a754b82dac511475b6276039471ccd17cc64aeb8`**.
- **Lean:** `implementation_renameModel` / `problem_spec_renameModel` /
  `correct_renameModel` in `Solution.lean`.

## What the function does (observable behavior)
The method issues a *sequence of schema-editor operations* (side effects) to
carry a model rename down to the database. The observable signal the F2P test
(`test_rename_model_with_db_table_noop`, `assertNumQueries(0)`) measures is the
*number / identity of operations issued*. We therefore model the function's
result as the **ordered list of emitted schema operations** (`List SchemaOp`).

Control flow @ base_commit:
1. `if self.allow_migrate_model(alias, new_model):` — outer applicability guard.
   When false the body is skipped → **no operations** (pre-existing behavior).
2. `schema_editor.alter_db_table(new_model, old_db_table, new_db_table)` — the
   main table rename (always emitted in the old code when the guard passes).
3. `for related_object in old_model._meta.related_objects:` … `alter_field(...)`
   — dependent FK columns; emits a (possibly empty) run of operations.
4. m2m loop: per local-m2m field (skipping self-referential / non-auto-created),
   `alter_db_table(...)` + `alter_field(...)`.

The patch adds, between (1) and (2):
```
old_db_table = old_model._meta.db_table
new_db_table = new_model._meta.db_table
if old_db_table == new_db_table:
    return
```
i.e. when the stored table name is unchanged by the rename, the *entire* body
(steps 2–4) is skipped → no operations. (The later refactor of the
`alter_db_table(...)` call to use the local vars is behavior-preserving.)

`database_backwards` merely swaps the names and calls `database_forwards`, so it
inherits the same fix — NOT an independently-fixed behavior (one prepatch).

## Type bijection (used by G-CONF / G-AX)
| Python | Lean |
|---|---|
| `self.allow_migrate_model(...)` truth value | `allowMigrate : Bool` |
| `old_model._meta.db_table` (a `str`) | `oldDbTable : String` |
| `new_model._meta.db_table` (a `str`) | `newDbTable : String` |
| `old_db_table == new_db_table` (str eq) | `oldDbTable == newDbTable` (`BEq String`) |
| `schema_editor.alter_db_table(new_model, old, new)` | `SchemaOp.renameTable old new` |
| ops emitted by the related-objects + m2m loops (UNCHANGED) | `tailOps : List SchemaOp` (abstract input) |
| the full sequence of operations issued | `result : List SchemaOp` |

### Modeling decision (tail abstraction)
The fix touches ONLY the control-flow guard. The related-objects and m2m loops
(steps 3–4) are **unchanged**; reconstructing them concretely would require
modeling `related_objects`, `local_many_to_many`, `get_field`, the
self-referential / auto-created `continue` conditions, etc. — all unchanged
machinery irrelevant to the discriminator. We therefore abstract everything the
old body would emit *after the main table rename* as a single opaque input
`tailOps : List SchemaOp`, passed through identically in the non-noop branch.
This keeps the result **grounded in inputs structurally** (the differ-branch
result is `SchemaOp.renameTable oldDbTable newDbTable :: tailOps`, a concrete cons
of the inputs — never an ungrounded oracle, directive 8) while modeling the
CHANGED control flow (the early-return guard) faithfully.

`SchemaOp` (`renameTable old new` for the main table rename; `other n` for any
other emitted operation, used only to populate `tailOps` in fuzzing).

## Callee provenance / flag deps
- No UNCHANGED callee needs an `opaque` signature or a consumed `_prop` axiom:
  the impl is self-contained structural control flow; the emitted operations are
  reified as `SchemaOp` data, not modeled by calling a real callee. Hence the
  `axioms` region is empty and `axiom_check.py` is a skip stub.
- No deep-model reference requiring G-AX validation (we model *that* an
  operation is emitted, never *what* `alter_db_table` does internally).

## G-CONF fuzz seed
`conf_seed = 14999` (pinned; see `conformance_check.py`).
