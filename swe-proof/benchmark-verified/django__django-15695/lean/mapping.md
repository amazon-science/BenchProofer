# mapping.md — django__django-15695

## Instance
- repo: django/django
- base_commit: 647480166bfe7532e8c471fef0146e3a17e6c0c9
- spec_provenance: cold (derived from problem_statement + gold patch + base-commit
  source only)

## The logical change
The gold patch adds a three-line guard to `RenameIndex.database_forwards`
(`django/db/migrations/operations/models.py`, in the `@@ -960,…` hunk). After the
operation has resolved the index it is renaming *from* (`old_index`) and just
before it would emit the rename, it now returns early when that index already
carries the target name:

```python
# django/db/migrations/operations/models.py @ base_commit (post-patch)
def database_forwards(self, app_label, schema_editor, from_state, to_state):
    model = to_state.apps.get_model(app_label, self.model_name)
    if not self.allow_migrate_model(schema_editor.connection.alias, model):
        return
    if self.old_fields:
        ...                                  # old_index from matching db index
    else:
        from_model_state = from_state.models[app_label, self.model_name_lower]
        old_index = from_model_state.get_index_by_name(self.old_name)
    # Don't alter when the index name is not changed.          <-- ADDED
    if old_index.name == self.new_name:                        <-- ADDED
        return                                                 <-- ADDED
    to_model_state = to_state.models[app_label, self.model_name_lower]
    new_index = to_model_state.get_index_by_name(self.new_name)
    schema_editor.rename_index(model, old_index, new_index)
```

The F2P test `test_rename_index_unnamed_index` applies the rename forward, then
backward (which restores the original auto-generated name), then forward again.
On the second forward the resolved `old_index.name` already equals
`self.new_name`, so without the guard the operation re-issues a rename to a name
that already exists and crashes ("relation … already exists"). With the guard the
second forward is a no-op.

## Modeled function
I model the **forward application decision** of the index-rename operation — the
choice of whether `database_forwards` emits the underlying rename and with which
index pair — as a total function of the data it has in hand at the decision
point. This is the smallest unit whose observable behavior the patch changes and
the F2P test pins. The body's only externally-observable effect is the (at most
one) `schema_editor.rename_index(model, old_index, new_index)` call; I model the
result as "which rename call is performed, if any."

## Symbol binding
| Lean symbol | Python source @ base_commit |
|---|---|
| `applyIndexRenameForward` | `RenameIndex.database_forwards` (`django/db/migrations/operations/models.py:933-965`) |
| `problem_spec_applyIndexRenameForward` | the post-condition the emitted rename action must satisfy |
| `Index` | the touched view of `django.db.models.Index` — only its `name` is read by the decision (`models.py:961,963-964`) |

## Type bijection (Lean ↔ Python) — used by G-CONF / G-AX
| Lean | Python | notes |
|---|---|---|
| `canMigrate : Bool` | `self.allow_migrate_model(schema_editor.connection.alias, model)` | `true ↔ migration permitted` (proceed); `false ↔ not permitted` (early `return`) |
| `oldIndex : Index` | `old_index` resolved by `get_index_by_name(self.old_name)` (or the `old_fields` matching index) | structure with `name : String`; `oldIndex.name ↔ old_index.name` |
| `newIndex : Index` | `new_index = to_model_state.get_index_by_name(self.new_name)` | structure with `name : String` |
| `newName : String` | `self.new_name` | the target name the operation renames *to* |
| result `: Option (Index × Index)` | the at-most-one `schema_editor.rename_index(model, old_index, new_index)` call | `none ↔ no rename emitted` (early return); `some (oldIndex, newIndex) ↔ rename(old_index, new_index) emitted` |

`Index` ↔ the Python index object is the touched-field bijection: only `.name` is
consulted by the changed decision, so `Index = { name : String }` is the faithful
view. Python `str` index names ↔ Lean `String` (identity).

## Callee provenance / flag deps
- No unchanged repo callee is *consumed* as an axiom. `allow_migrate_model`,
  `get_index_by_name`, `apps.get_model` all run BEFORE the decision and produce
  the data the decision reads (`canMigrate`, `oldIndex`, `newIndex`); they enter
  the model as inputs, not as axiomatized contracts. The single observable effect
  (`rename_index`) is the result the spec pins. So there is no `opaque` callee and
  no `axiom <callee>_prop`; the `axioms` region is empty and `axiom_check.py` is a
  skip stub.
- Flag dependency: the `old_fields` vs `old_name` split upstream only changes HOW
  `old_index` is computed (named lookup vs matching the unnamed index by columns);
  both paths converge to a single `old_index` with a `.name`, which is exactly the
  datum the changed guard reads. The decision is therefore independent of which
  upstream branch produced `old_index`; G-CONF fuzzes the resolved `old_index.name`
  directly (covering both branches' outputs).

## G-CONF fuzz seed
- pinned seed: `15695`
- ≥10^5 fuzzed `(canMigrate, oldIndexName, newName, newIndexName)` tuples; names
  drawn from a small pool so `oldIndexName == newName` collisions (the
  discriminating equal-name branch the patch adds) occur frequently, with
  `canMigrate` mixed true/false. The oracle drives the REAL patched
  `RenameIndex.database_forwards` against recording fakes (see
  `conformance_check.py`).
