# mapping.md — django__django-13401

## Symbol binding (file:line @ base_commit `453967477e`)
- `django/db/models/fields/__init__.py:516` `Field.__eq__`  → `fieldEq` / `problem_spec_fieldEq` / `implementation_fieldEq`
- `django/db/models/fields/__init__.py:522` `Field.__lt__`  → `fieldLt` / `problem_spec_fieldLt` / `implementation_fieldLt`
- `django/db/models/fields/__init__.py:528` `Field.__hash__` → `fieldHashKey` / `problem_spec_fieldHashKey` / `implementation_fieldHashKey`

All three are methods of the same `Field` class and are changed by the gold
patch together; they are three independently-observable behaviors (equality,
ordering, hashing) over the SAME underlying field identity.

## Type bijection (Lean ↔ Python)  — used by G-CONF / G-AX
A `Field` instance is modeled by `FieldId`, capturing exactly the attributes the
three methods read:

| Lean (`FieldId`) | Python attribute read | notes |
|---|---|---|
| `creationCounter : Int` | `self.creation_counter` | monotonically-assigned int counter |
| `model : Option (String × String)` | `getattr(self, 'model', None)` resp. `hasattr(self, 'model')` + `self.model._meta.(app_label, model_name)` | `none` ↔ field has NO `model` attribute (`hasattr == False`); `some (appLabel, modelName)` ↔ field is attached to a model whose `_meta.app_label` / `_meta.model_name` are those strings |

Justification for `model ↦ Option (String × String)`:
- `__eq__` compares the model *objects* (`getattr(...,'model',None)`). A model
  class is uniquely identified in Django by `(_meta.app_label, _meta.model_name)`
  — two distinct model classes never share that pair, so model-object identity is
  in bijection with the `(app_label, model_name)` pair. `none ↔ none` mirrors the
  `getattr default None` comparison.
- `__lt__` and `__hash__` read `hasattr(self, 'model')` (↔ `isSome`) and, when
  present, exactly `self.model._meta.app_label` and `self.model._meta.model_name`.

### Result-type bijections
- `__eq__` / `__lt__` → Python `bool` ↔ Lean `Bool`. (The `NotImplemented`
  branch is taken only for non-`Field` `other`; the model is `Field`-vs-`Field`
  only, the only case the F2P test and issue exercise.)
- `__hash__` → Python `int` `hash(t)` of the tuple
  `t = (creation_counter, app_label_or_None, model_name_or_None)`. The observable
  contract of `__hash__` is the *hash key* `t` (Python guarantees
  `a == b ⟹ hash(a) == hash(b)`, and the F2P test relies on distinct keys giving
  distinct hashes). We model the key tuple
  `Int × Option String × Option String` directly — the injective key that the
  field hashes — rather than Python's opaque `hash()` integer. G-CONF compares
  the modeled key against the real `(creation_counter, app_label_or_None,
  model_name_or_None)` tuple the patched `__hash__` constructs.

## Callee provenance / flag deps
None. The fix is straight-line attribute reads + comparisons; it calls no
unchanged repo callee that needs an axiom. `model._meta.app_label` /
`model._meta.model_name` are plain attribute reads, captured by the `FieldId`
bijection (R), not axiomatized. → no `opaque`/`axiom` decls; `axiom_check.py` is a
skip stub.

## G-CONF fuzz seed
seed = 13401 (pinned in `conformance_check.py`).
