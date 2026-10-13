# mapping.md — django__django-15973

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 2480554dc4ada4ecf3f6a08e318735a2e50783f3`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of the one foreign callee (deeply modeled, A-reference).

Repo file under change: `django/db/migrations/autodetector.py`.
`spec_provenance: cold` (derived from problem_statement + gold patch + repo
source at base_commit only).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `relationDependencies (f, appLabel, modelName)` | `Autodetector._get_dependencies_for_foreign_key(app_label, model_name, field, project_state)` — `django/db/migrations/autodetector.py:1397` (body 1398-1432) | the modeled changed function: the list of migration dependencies a relational field induces |
| `resolveRef (m, appLabel, modelName)` *(deep model — A-reference)* | `resolve_relation(model, app_label, model_name)` — `django/db/migrations/utils.py:27` | unchanged callee: turn a model reference (string or model object) into an `(app_label, object_name)` pair; modeled deeply, validated `resolveRef == resolve_relation` by axiom_check.py (G-AX) |
| `RelField` | the relevant attributes of the `field` argument: `field.remote_field.model` (`target`), `field.remote_field.through` (`through`), `field.swappable_setting` (`swappable`) | the touched fields of the rich `Field`/`ForeignObjectRel` object |
| `RelRef` | a model reference: a `str` (`"app.Model"`, bare `"Model"`, or the recursive sentinel `"self"`) OR a resolved model object exposing `_meta.app_label` / `_meta.model_name` | the argument type of `resolve_relation` |
| `Dep` | a dependency 4-tuple `(app_label, object_name, field_name, create)` Django appends to `dependencies` | one migration dependency |

The modeled function takes a fourth argument `project_state` in the repo; it is
consulted ONLY in the `else` branch reached when `field.remote_field` has no
`model` attribute. Every relational field this function is called on (FK, O2O,
M2M — including the M2M-with-`through` of the issue) DOES expose
`remote_field.model`, so that branch is dead for the modeled inputs and
`project_state` is never read on the F2P path; it is therefore omitted from the
model (see §2, "remote_field_model resolution"). G-CONF drives the REAL function
with field objects that expose `remote_field.model`, exercising the live path.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a model reference passed to `resolve_relation` | `RelRef` | `"self"` ↔ `.selfRef`; `"app.Model"` ↔ `.qualified "app" "Model"`; bare `"Model"` (no dot) ↔ `.bare "Model"`; a model object with `_meta.(app_label, model_name)` ↔ `.resolved app_label model_name` |
| `(app_label, object_name)` pair returned by `resolve_relation` | `String × String` | componentwise string identity |
| the dependency 4-tuple `(app, obj, field, create)` | `Dep` | `app`↔`.app`, `obj`↔`.name`, `field` (always `None` here)↔`.fieldName = none`, `create` (always `True` here)↔`.create = true` |
| `field.swappable_setting` (`str` or `None`) | `Option String` (`f.swappable`) | `None` ↔ `none`; a setting name `s` ↔ `some s` |
| `field.remote_field.model` | `RelRef` (`f.target`) | as the model-reference row above |
| `field.remote_field.through` (model ref or `None`) | `Option RelRef` (`f.through`) | `None` ↔ `none`; a through ref `t` ↔ `some (RelRef of t)` |

**`remote_field_model` resolution.** In the repo the first block sets
`remote_field_model = field.remote_field.model` whenever the field exposes a
`model` attribute (true for every relational field type). The model's `f.target`
IS that `field.remote_field.model`. The `else` (relation-table reverse lookup
via `project_state.relations`) is unreachable for these fields, so it is not
modeled — the omission is sound because `project_state` is never read on the
modeled path (G-CONF passes a real field with `remote_field.model`, never
forcing the `else`).

`str.lower()` ↔ `String.toLower` (per-character `Char.toLower`): both lower-case
ASCII `A–Z`; the object names in play (`"Model"`, `"Contract"`, …) are ASCII, so
the bijection is exact on the relevant alphabet (G-AX fuzzes mixed-case ASCII).

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `resolveRef` deep model ↔ `resolve_relation` (A-reference)
**Callee:** `django.db.migrations.utils.resolve_relation` (UNCHANGED by the
patch). The function under change calls it twice — once for the base dependency
and once (the patched call) for the through dependency. It is modeled **deeply**
by `resolveRef` (pure region); there is **no consumed `resolve_relation` axiom**.
Source at base_commit (`django/db/migrations/utils.py:27-50`):

```python
def resolve_relation(model, app_label=None, model_name=None):
    if isinstance(model, str):
        if model == RECURSIVE_RELATIONSHIP_CONSTANT:   # "self"
            if app_label is None or model_name is None:
                raise TypeError(...)
            return app_label, model_name
        if "." in model:
            app_label, model_name = model.split(".", 1)
            return app_label, model_name.lower()
        if app_label is None:
            raise TypeError(...)
        return app_label, model.lower()
    return model._meta.app_label, model._meta.model_name
```

The four `resolveRef` arms mirror the four returns exactly:
`.selfRef → (appLabel, modelName)`; `.qualified a n → (a, n.toLower)`
(the `"app.Model".split(".",1)` then `.lower()` case);
`.bare n → (appLabel, n.toLower)`; `.resolved a n → (a, n)`
(the model-object case, `_meta.app_label`/`_meta.model_name` already lower).
The two `TypeError` paths require `app_label`/`model_name = None`; the call sites
always pass both (`app_label`, `model_name` are method parameters), so those
paths are unreachable from the modeled function and need not be modeled.

**Soundness check (G-AX):** `axiom_check.py` imports the REAL
`resolve_relation`, runs it on boundary references (`"self"`, qualified,
bare, mixed-case, dotted-multi, a fake model object exposing `_meta`) plus
randomized fuzz strings, and asserts `resolve_relation(...) == resolveRef(...)`
for every observation. stdlib + django only. Exit 0 iff sound.

### 3.2 No consumed axiom
`relationDependencies` consumes no `axiom`. The only foreign callee is
`resolve_relation` (deep model, §3.1, A-reference). The rest of the function —
the swappable branch, building the base dependency, and appending the through
dependency — is concrete control/data flow (I/R), transliterated and
differential-tested by G-CONF.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`15973`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `resolveRef`/`baseDep`/`relationDeps` (R/I-tagged ops) to Python
and calls the REAL `_get_dependencies_for_foreign_key` (the patched oracle) on
duck-typed field objects bridged via the §2 table. Because the modeled function
reads only `field.remote_field.{model,through}` and `field.swappable_setting`
(never `project_state` on the modeled path), the oracle is exercised directly,
DB-free — so this bundle has a runnable R/I shadow (`conf_skip = false`).
