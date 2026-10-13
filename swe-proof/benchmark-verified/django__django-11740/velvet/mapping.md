# mapping.md — django__django-11740

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 003bb34b218adb23d1a7e67932a6ba9b3c4dcc81`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of the one foreign computation (deeply modeled, an
A-reference).

Repo file under change: `django/db/migrations/autodetector.py`.
`spec_provenance: cold` (derived from problem_statement + gold patch + repo
source at base_commit only).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `alteredFieldDependencies (isReferential, f)` | the per-field body of `MigrationAutodetector.generate_altered_fields` — `django/db/migrations/autodetector.py:904` (the `dependencies` value the field's altered-field operation is created with, gold lines 912/940/975) | the modeled changed function: the ordering dependencies attached to the operation that alters one field |
| `relationDeps (f)` *(deep model — A-reference)* | `MigrationAutodetector._get_dependencies_for_foreign_key(field)` — `django/db/migrations/autodetector.py:1060` | UNCHANGED callee: the set of `(app, object_name, None, True)` dependencies a referential field induces; modeled deeply, validated `relationDeps == _get_dependencies_for_foreign_key` by axiom_check.py (G-AX) |
| `RelField` | the relevant referential attributes of the `new_field` argument: `new_field.remote_field.model._meta.{app_label,object_name}` (`targetApp`/`targetObj`), the *effective* explicit-through model (`through`), and `new_field.swappable_setting` (`swappable`) | the touched fields of the rich `Field`/`ForeignObjectRel` object |
| `Dep` | a dependency 4-tuple `(app_label, object_name, field_name, create)` Django appends to `dependencies` | one ordering dependency |
| `isReferential : Bool` | the predicate `hasattr(new_field, "remote_field") and getattr(new_field.remote_field, "model", None)` (`autodetector.py:917`) under which the gold `dependencies.extend(...)` (gold line 940) runs | whether the new field references another model |

The function `generate_altered_fields` iterates over changed fields and, for the
referential ones, attaches the FK dependencies to the emitted `AlterField`
operation. The patch adds exactly three things (gold patch): initialise
`dependencies = []` (line 912), `dependencies.extend(self._get_dependencies_for_foreign_key(new_field))`
inside the `remote_field.model` block (line 940), and pass
`dependencies=dependencies` to `add_operation` (line 975). The model captures
the value of `dependencies` that the operation is created with, as a function of
the field's referential configuration.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `hasattr(new_field, "remote_field") and getattr(new_field.remote_field, "model", None)` (truthy ⇒ referential) | `isReferential : Bool` | non-relational field (`IntegerField`, `CharField`, …) ↔ `false`; relational field exposing `remote_field.model` (FK, O2O, M2M) ↔ `true` |
| `new_field.remote_field.model._meta.app_label` / `.object_name` | `RelField.targetApp` / `.targetObj : String` | componentwise string identity; `object_name` is the CamelCase class name |
| `new_field.swappable_setting` (`str` or `None`) | `RelField.swappable : Option String` | `None` ↔ `none`; a setting name `s` (e.g. `"AUTH_USER_MODEL"`) ↔ `some s` |
| the *effective* through dependency: `field.remote_field.through` when present **and** `not through._meta.auto_created`, taken as `(through._meta.app_label, through._meta.object_name)` | `RelField.through : Option (String × String)` | no `through`, or an **auto-created** through (plain M2M) ↔ `none`; an **explicit** through model `T` (with `auto_created = False`) ↔ `some (T._meta.app_label, T._meta.object_name)` |
| the dependency 4-tuple `(app, obj, field, create)` | `Dep` | `app`↔`.app`, `obj`↔`.name`, `field` (always `None` here)↔`.fieldName = none`, `create` (always `True` here)↔`.create = true` |

The `RelField.through` carrier folds the callee's two-part test
`getattr(field.remote_field, "through", None) and not field.remote_field.through._meta.auto_created`
into a single "is there an *effective* (explicit) through?" — the only
observable distinction at this commit. G-AX fuzzes both auto-created and
explicit through configurations against the real callee, and G-CONF drives the
real callee with both, so the fold is checked, not assumed.

`isReferential` collapses the v3.0 referential predicate. The gold
`dependencies.extend(...)` runs only inside the `if hasattr(new_field,
"remote_field") and getattr(new_field.remote_field, "model", None):` block; a
non-relational field never reaches it, so `dependencies` stays `[]`. That is
exactly `out = if isReferential then relationDeps f else []`.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `relationDeps` deep model ↔ `_get_dependencies_for_foreign_key` (A-reference)
**Callee:** `MigrationAutodetector._get_dependencies_for_foreign_key(field)`
(UNCHANGED by the patch). The patch *adds a call* to this existing method from
`generate_altered_fields`; it does not modify the method. It is modeled
**deeply** by `relationDeps` (with `baseDep`/`mkDep`, pure region); there is
**no consumed axiom**. Source at base_commit (`autodetector.py:1060-1078`):

```python
def _get_dependencies_for_foreign_key(self, field):
    swappable_setting = getattr(field, 'swappable_setting', None)
    if swappable_setting is not None:
        dep_app_label = "__setting__"
        dep_object_name = swappable_setting
    else:
        dep_app_label = field.remote_field.model._meta.app_label
        dep_object_name = field.remote_field.model._meta.object_name
    dependencies = [(dep_app_label, dep_object_name, None, True)]
    if getattr(field.remote_field, "through", None) and not field.remote_field.through._meta.auto_created:
        dependencies.append((
            field.remote_field.through._meta.app_label,
            field.remote_field.through._meta.object_name,
            None,
            True,
        ))
    return dependencies
```

`relationDeps`/`baseDep` mirror this exactly:
* `baseDep`: `swappable is some s ⇒ ("__setting__", s, None, True)`; else
  `(targetApp, targetObj, None, True)` — the swappable test and base tuple.
* the through arm: `through = none ⇒ [baseDep]` (no through, or an auto-created
  through — both filtered out by the `none` carrier, §2); `through = some (ta,
  to_) ⇒ [baseDep, (ta, to_, None, True)]` (an explicit through model).

**Soundness check (G-AX):** `axiom_check.py` imports the REAL
`_get_dependencies_for_foreign_key`, builds real relational fields (FK, O2O, M2M
auto-created through, M2M explicit through, swappable FK to `AUTH_USER_MODEL`)
across boundary + randomized app/object/through configurations, and asserts
`_get_dependencies_for_foreign_key(field) == relationDeps(RelField of field)`
for every observation. django-only. Exit 0 iff sound.

### 3.2 No consumed axiom
`alteredFieldDependencies` consumes no `axiom`. The only foreign computation is
`_get_dependencies_for_foreign_key` (deep model, §3.1, A-reference). The rest of
the modeled function — the `dependencies = []` init and the referential-branch
guard — is concrete control/data flow (I/R), transliterated and
differential-tested by G-CONF.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`11740`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `relationDeps`/`baseDep`/`mkDep` and the referential-branch guard
to Python, and compares against the ORACLE: the patched
`generate_altered_fields`' attached dependencies, observed by driving the REAL
`MigrationAutodetector` over in-memory `ProjectState`s (DB-free, exactly as the
F2P test's `get_changes` does) and reading the resulting `AlterField`
operation's `_auto_deps`. Because the modeled value depends only on the new
field's referential configuration, the oracle is exercised directly. The bundle
has a runnable R/I shadow (`conf_skip = false`).
