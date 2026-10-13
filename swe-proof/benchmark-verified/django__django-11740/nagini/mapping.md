# mapping.md — django__django-11740

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 003bb34b218adb23d1a7e67932a6ba9b3c4dcc81`, states the type
abstraction, and gives the provenance of the one axiom.

Repo file under change: `django/db/migrations/autodetector.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `altered_field_dependencies(new_field)` | the per-field body of `MigrationAutodetector.generate_altered_fields` — `django/db/migrations/autodetector.py:904` (loop body lines 909-978) — specifically the `dependencies` value the emitted `operations.AlterField(...)` is created with via `add_operation(..., dependencies=dependencies)` | the modeled changed function: what dependency list the altered-field operation carries |
| `fk_dependencies(field)` *(axiom — A-consumed)* | `MigrationAutodetector._get_dependencies_for_foreign_key(self, field)` — `django/db/migrations/autodetector.py:1060` | unchanged helper the patch calls (`dependencies.extend(self._get_dependencies_for_foreign_key(new_field))`) to compute a relational field's ordering dependencies |
| `FieldDef.is_relation` | the truth of `hasattr(new_field, "remote_field") and getattr(new_field.remote_field, "model", None)` (autodetector.py:917) — equivalently a model field's `is_relation` / having a resolvable `remote_field.model` | the single touched property of the new field definition: whether it references another model |

The pre-patch repo facts the change addresses (for the refinement audit, not
referenced from the consumer spec view): `generate_altered_fields` built the
`operations.AlterField(...)` and called `self.add_operation(app_label, ...)`
with **no** `dependencies` argument (autodetector.py:966-973 pre-patch), so
`add_operation`'s `dependencies=None` became `operation._auto_deps = [] `
(autodetector.py:439). When a non-relational field was altered into a relational
one, the emitted operation therefore carried no dependency on the referenced
model, and the migration planner raised `ValueError: Related model '<app.Model>'
cannot be resolved`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the new field definition object (`new_field`) | `FieldDef` with the single boolean `is_relation` | `FieldDef.is_relation == True` ⇔ `hasattr(new_field, "remote_field") and getattr(new_field.remote_field, "model", None)` is truthy (the patch's relation guard, autodetector.py:917). No other field attribute is observed by the modeled behaviour. |
| the `dependencies` list attached to the emitted `AlterField` operation (a `list` of 4-tuples `(app_label, object_name, field_name, True/False)`) | `PSeq[int]` — each dependency tuple is an opaque `int` code | `len(deps)` ↔ `len(Result())`; `deps == []` ↔ `len(Result()) == 0`; list `extend`/concatenation ↔ `PSeq` `+`. The load-bearing observable is **which dependencies are present**, in particular whether the list is non-empty (the F2P test asserts the dependency set, whose presence/absence is exactly what the bug changed). |
| `dependencies = []`; `dependencies.extend(self._get_dependencies_for_foreign_key(new_field))` | `dependencies = PSeq()`; `dependencies = dependencies + fk_dependencies(new_field)` | empty-list init ↔ empty `PSeq`; `list.extend(callee(...))` ↔ `PSeq + fk_dependencies(...)` |

The model deliberately abstracts away the `remote_field.model` rename handling,
the `through` handling, the m2m/concrete split, and the `ask_not_null_alteration`
branch (autodetector.py:917-978): none of them changes the dependency value the
operation is created with. The single behavioural delta the patch introduces —
seed `dependencies = []`, extend it with the FK dependencies when the new field
is relational, and pass it to the operation — is what the model captures.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `fk_dependencies` ↔ `_get_dependencies_for_foreign_key` (A-consumed)
**Callee:** `MigrationAutodetector._get_dependencies_for_foreign_key(self, field)`
(`django/db/migrations/autodetector.py:1060-1077`), unchanged by the patch:

```python
def _get_dependencies_for_foreign_key(self, field):
    # Account for FKs to swappable models
    swappable_setting = getattr(field, 'swappable_setting', None)
    if swappable_setting is not None:
        dep_app_label = "__setting__"
        dep_object_name = swappable_setting
    else:
        dep_app_label = field.remote_field.model._meta.app_label
        dep_object_name = field.remote_field.model._meta.object_name
    dependencies = [(dep_app_label, dep_object_name, None, True)]
    if getattr(field.remote_field, "through", None) and not field.remote_field.through._meta.auto_created:
        dependencies.append((...))
    return dependencies
```

**Axiom encoded (the WEAKEST the proof needs):** for any relational field
definition, the returned list is **non-empty** — `len(Result()) > 0`. This holds
unconditionally: the very first statement after the swappable branch is
`dependencies = [(dep_app_label, dep_object_name, None, True)]`, a one-element
list; the optional `through` entry only ever appends. The result is never empty
for a field that reaches this helper. The model does not over-claim the *content*
of the dependencies (which app/object) — only that at least one exists, which is
exactly the property the bug violated (the operation got zero dependencies) and
the F2P test observes (a non-empty dependency on the referenced app).

**Soundness check (G-AX):** `axiom_check.py` configures Django exactly as the
autodetector test module does, builds six resolved relational field shapes — FK
to another app, FK to the same app, OneToOne, m2m with auto-created through, m2m
with an explicit (non-auto-created) through, and FK to the swappable user model
(the `swappable_setting` branch) — and asserts
`len(_get_dependencies_for_foreign_key(field)) > 0` for each. It imports only
Django (the framework under test) and the standard library; exit 0 iff sound. It
binds the helper by parameter name so it runs against the 3.0 single-argument
signature in the eval container (and any later arity in a host smoke test).
