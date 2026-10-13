# mapping.md — django__django-15973

## Symbol binding (file:line @ base_commit 2480554dc4ada4ecf3f6a08e318735a2e50783f3)
Modeled function: `_get_dependencies_for_foreign_key`
(`django/db/migrations/autodetector.py:1397-1431`, the static method that
returns the list of migration dependencies a relational field induces). The gold
patch is a one-line change at line 1424: the second ("through") dependency is
resolved from the reference that denotes the *intermediary* model
(`field.remote_field.through`) instead of from `remote_field_model` (the
reference that denotes the relation's *target* model).

Lean modeled function name: `relationDependencies` (neutral — names the
*behavior* "the dependencies a relational field induces", not the patched symbol;
see G-LEAK below).

| Lean symbol | Python binding (file:line @ base) |
|---|---|
| `relationDependencies` (modeled value) | return value of `_get_dependencies_for_foreign_key`, `autodetector.py:1397-1431` |
| `targetRef : ModelRef` | `remote_field_model` — `field.remote_field.model` if present, else the `"app.Model"` string assembled from `project_state.relations`, `autodetector.py:1398-1408` |
| `throughRef : Option ModelRef` | `field.remote_field.through` when `getattr(field.remote_field, "through", None)` is truthy, else `None`, `autodetector.py:1421-1424` (POST-patch line 1424 = `field.remote_field.through`) |
| `swappableSetting : Option String` | `getattr(field, "swappable_setting", None)`, `autodetector.py:1410-1413` |
| `scopeApp : String` | `app_label` parameter (owning model's app), `autodetector.py:1397` |
| `scopeName : String` | `model_name` parameter (owning model's name), `autodetector.py:1397` |
| `modelRefToPair` | `resolve_relation(model, app_label, model_name)`, `django/db/migrations/utils.py:27-51` (UNCHANGED callee, deep-modeled — A-reference) |
| `result : List (String × String)` | `dependencies`, the list returned; each real tuple is `(app_label, object_name, None, True)` — the modeled pair is the `(app_label, object_name)` head; the constant `(None, True)` tail is invariant (see frame note) |

## Lean ↔ Python type bijection (used by G-CONF and G-AX)
| Python | Lean |
|---|---|
| a model reference: a `str` (`"app.Object"`, bare `"Object"`, or `"self"`) OR a model class with `_meta.app_label` / `_meta.model_name` | `ModelRef` (`.str s` / `.concrete app obj`) |
| `str.lower()` | `opaque lower : String → String` — the object-name case normalization, left ABSTRACT. Python `str.lower` is a full Unicode case fold (`'Ä'`→`'ä'`, `'Σ'`→`'σ'`, `'İ'`→`'i̇'`, possibly length-changing); no concrete Lean per-character fold reproduces it (Lean `Char.toLower` folds ASCII only), so committing to one would be unfaithful on non-ASCII names. The opaque symbol is bound to the REAL `str.lower` by the G-AX A-reference validation (the executable replica interprets `lower` as Python `str.lower`); the Lean proof never inspects `lower`'s behavior, so no axiom about it is consumed. |
| `model.split(".", 1)` (split on FIRST dot only) | `splitFirstDot` (`splitOn "."` then re-`intercalate "."` the remainder) |
| `resolve_relation(model, app_label, model_name)` → `(app_label, object_name)` | `modelRefToPair m scopeApp scopeName : String × String` |
| `getattr(field, "swappable_setting", None)` | `swappableSetting : Option String` |
| `getattr(field.remote_field, "through", None)` truthiness + value | `throughRef : Option ModelRef` |
| `dependencies` (list of 4-tuples) | `result : List (String × String)` (the resolved `(app_label, object_name)` head of each tuple) |

### Frame / projection note
Each real dependency is a 4-tuple `(app_label, object_name, None, True)`. The
`None` (field name) and `True` (create-flag) components are **constant** for both
dependencies the modeled branch produces (`None, True` in both the target and
through appends, `autodetector.py:1420,1425`). They are input-independent
literals, carry no behavior the fix touches, and are therefore projected out of
the model; the modeled pair is exactly the `(app_label, object_name)` head, which
is the only component the fix affects. G-CONF re-attaches the constant tail when
comparing against the real return value.

## resolve_relation — the deep-modeled (A-reference) callee
`resolve_relation` (utils.py:27-51) is UNCHANGED by the patch; the fix only
changes WHICH reference is passed to it for the through dependency. Its behavior:
  * a model class → `(model._meta.app_label, model._meta.model_name)`;
  * `"self"` (RECURSIVE_RELATIONSHIP_CONSTANT, `related.py:40`) → `(app_label, model_name)`;
  * `"app.Object"` → `model.split(".", 1)` then `(app, object.lower())`;
  * bare `"Object"` → `(app_label, object.lower())`.
Modeled deeply as `modelRefToPair`. This is an **A-reference** (validated `==`
real `resolve_relation` by G-AX), NOT a consumed axiom: no `axiom _prop` is
shipped. `app_label`/`model_name` are non-`None` in this call site (the owning
model always has a name), so the recursive-relation `TypeError` branches are
unreachable here and not modeled (the F2P inputs never hit them).

### The abstract case fold (`opaque lower`)
`resolve_relation` lower-cases the object-name segment with Python `str.lower`
— a full Unicode case fold (`'Ä'.lower() = 'ä'`, `'İ'.lower() = 'i̇'` which even
changes length). Lean has no built-in equal fold (`Char.toLower` is
ASCII-only), so the model does NOT approximate it: `lower` is declared
`opaque : String → String` in the axioms region and the contract is stated
relative to it. This keeps the spec faithful on EVERY input, non-ASCII object
names included — the spec pins the dependency-construction rule (which
reference feeds the resolver for each dependency, in which scope), with the
fold itself abstracted exactly as the real helper's normalization. G-AX
validates the binding `lower = str.lower` executably: its replica of
`modelRefToPair` interprets `lower` as the real `str.lower` and is checked `==`
the real `resolve_relation` on 50k+ inputs. No `axiom` about `lower` is
consumed (the correctness proof never unfolds it).

## Callee provenance + flag deps
- `resolve_relation` — `django/db/migrations/utils.py:27`, unchanged. A-reference.
- Flag dependency: the second dependency is appended iff
  `getattr(field.remote_field, "through", None)` is truthy (`throughRef = some _`).
  A swappable field instead produces the `("__setting__", setting)` target head
  (`swappableSetting = some setting`); modeled in the spec's first-entry branch.

## Pinned G-CONF fuzz seed
`15973`.
