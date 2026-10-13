# refinement.md — django__django-15695

Maps every operation in `implementation_applyIndexRenameForward` to its
`patch.diff` counterpart. The patch adds a guard to the forward-application
decision of the index-rename operation (see mapping.md). Tags: **R**
type-refinement, **A-consumed** proof uses a callee axiom, **A-reference**
deep-modeled changed op validated == real callee, **I** identical concrete op.

## Patch (post-patch)
```python
# django/db/migrations/operations/models.py — RenameIndex.database_forwards
def database_forwards(self, app_label, schema_editor, from_state, to_state):
    model = to_state.apps.get_model(app_label, self.model_name)
    if not self.allow_migrate_model(schema_editor.connection.alias, model):
        return
    if self.old_fields:
        ...                                   # old_index from matching db index
    else:
        from_model_state = from_state.models[app_label, self.model_name_lower]
        old_index = from_model_state.get_index_by_name(self.old_name)
    # Don't alter when the index name is not changed.            <-- ADDED
    if old_index.name == self.new_name:                          <-- ADDED
        return                                                   <-- ADDED
    to_model_state = to_state.models[app_label, self.model_name_lower]
    new_index = to_model_state.get_index_by_name(self.new_name)
    schema_editor.rename_index(model, old_index, new_index)
```

## Operation correspondence
| # | Lean op (`implementation_applyIndexRenameForward`) | patch.diff / governed op | tag | note |
|---|---|---|---|---|
| 1 | `if canMigrate = false then return none` | `if not self.allow_migrate_model(...): return` | R | `canMigrate : Bool ↔ allow_migrate_model(...) : bool`; unchanged guard, carried so the decision is total. No effect emitted ⇒ `none`. |
| 2 | `if oldIndex.name = newName then return none` | `if old_index.name == self.new_name: return` (the ADDED guard) | I | the new guard, modeled identically; `oldIndex.name : String ↔ old_index.name : str`, `newName : String ↔ self.new_name : str`. THIS is the line the patch adds (prepatch omits it). |
| 3 | `return some (oldIndex, newIndex)` | `schema_editor.rename_index(model, old_index, new_index)` | R | the single observable effect; modeled as the emitted `(oldIndex, newIndex)` relabel pair. `newIndex : Index ↔ new_index = get_index_by_name(self.new_name)`. |

The upstream `old_fields`-vs-`old_name` split (how `old_index` is computed) is
NOT modeled separately: both branches converge to one `old_index` whose `.name`
is the only datum the changed decision reads, so it enters the model as the input
`oldIndex` (mapping.md). Every modeled op is R or I; **no A row** (no axiom
consumed, no deep-model reference). Therefore `meta.json axioms = []`,
`deep_model_references = []`, and `axiom_check.py` is a skip stub.

## R/I legs ⇒ G-CONF
The whole impl is R/I, so `conformance_check.py` mechanically differential-tests
the impl shadow against the REAL patched `RenameIndex.database_forwards`
(driven over recording fakes for state + schema-editor) over ≥10^5 fuzzed inputs.
`conf_skip = false`. Verified: 0 disagreements against the patched tree;
~10% disagreements against the unpatched tree (the equal-name branch), confirming
the spec sees the bug.

## Prepatch = the real bug
`Solution_prepatch.lean` omits op #2 (the added guard): after the migration-permitted
check it unconditionally returns `some (oldIndex, newIndex)`. When migration is
permitted and `oldIndex.name = newName` the impl emits the relabel, but the spec's
second clause (`canMigrate = true → oldIndex.name = newName → result = none`)
demands `none`. The carried gold proof fails to typecheck on exactly that
discriminating clause (`refine_2`) — precisely the behavior the FAIL_TO_PASS test
`test_rename_index_unnamed_index` asserts: re-applying the forward rename when the
index already bears the target name must be a no-op (pre-patch it crashed with
"relation … already exists"). The spec is byte-identical between the two files
(only the impl body differs).

## patch.diff == gold
`patch.diff` is the gold patch verbatim (the three-line guard in
`RenameIndex.database_forwards`); it applies at `base_commit` and the harness
resolves.
