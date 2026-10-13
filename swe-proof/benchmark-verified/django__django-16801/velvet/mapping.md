# mapping.md — django__django-16801

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 3b62d8c83e3e48d2ed61cfa32a61c56d9e030293`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance + flag dependencies.

Repo file under change: `django/db/models/fields/files.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `registerInitHandler (isAbstract hasWidthField hasHeightField : Bool)` | `ImageField.contribute_to_class` — `django/db/models/fields/files.py:438-445` (the registration decision at body line 444-445) | modeled changed function #1: the decision of whether to attach the post-initialization dimension-synchronization handler for a model class |
| `dimensionWrites (deferred force hasFile hasWidthField widthFilled hasHeightField heightFilled : Bool)` | `ImageField.update_dimension_fields` — `django/db/models/fields/files.py:447-503` | modeled changed function #2: which companion dimension fields one synchronization pass writes back |
| `shouldRegister` | the registration guard `not cls._meta.abstract and (self.width_field or self.height_field)` (`files.py:444` post-patch) | pure spec: the registration predicate |
| `dimUpdate` / `DimWrites` | the body of `update_dimension_fields` from its early-return guards through the two final `setattr` writes (`files.py:461-503`) | pure spec: the set of companion fields written by one pass |

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| `cls._meta.abstract` (a truthy/falsy flag) | `isAbstract : Bool` | Python `bool(cls._meta.abstract)` ↔ the Lean `Bool` |
| `self.width_field` (a field name string or `None`/`""`) | `hasWidthField : Bool` | Python truthiness `bool(self.width_field)` ↔ the Lean `Bool`; only the *presence* of a declared width field is observable by the registration/assignment decisions |
| `self.height_field` (a field name string or `None`/`""`) | `hasHeightField : Bool` | Python truthiness `bool(self.height_field)` ↔ the Lean `Bool` |
| `self.attname in instance.__dict__` (value not deferred) | `deferred : Bool` | Python `self.attname not in instance.__dict__` ↔ `deferred = True`; i.e. `deferred` is the negation of "the value is loaded" |
| `force` parameter | `force : Bool` | Python `bool(force)` ↔ the Lean `Bool` |
| `bool(file)` where `file = getattr(instance, self.attname)` | `hasFile : Bool` | Python truthiness of the bound file object ↔ the Lean `Bool` |
| `getattr(instance, self.width_field)` is truthy | `widthFilled : Bool` | Python `bool(getattr(instance, self.width_field))` ↔ the Lean `Bool`; only consulted when `hasWidthField` |
| `getattr(instance, self.height_field)` is truthy | `heightFilled : Bool` | Python `bool(getattr(instance, self.height_field))` ↔ the Lean `Bool`; only consulted when `hasHeightField` |
| the registration decision (whether `signals.post_init.connect(self.update_dimension_fields, sender=cls)` runs) | `out : Bool` of `registerInitHandler` | `True` ↔ the connect call executes; `False` ↔ it is skipped |
| the set of companion fields written by one pass (`setattr(instance, self.width_field, …)` / `setattr(instance, self.height_field, …)`) | `out : DimWrites` of `dimensionWrites` | `writeWidth = True` ↔ the `setattr` to the width field executes; `writeHeight = True` ↔ the `setattr` to the height field executes |

All observables are Booleans because both modeled decisions branch only on the
truthiness of these configuration facts; the concrete field-name strings and the
concrete width/height *values* assigned are immaterial to the control-flow
decision the patch changes. (The value actually assigned — `file.width` /
`file.height` or `None` — is unchanged by the patch and is not modeled.)

## 3. Callee provenance and flag dependencies

**No consumed axioms, no deep-model references.** Both modeled functions are
pure Boolean decision logic over the inputs above. The underlying observations
(model abstractness, declared companion fields, deferred state, file presence,
companion-field population, force flag) are read directly from the field /
instance and are *inputs* to the decision, not callees with contracts the proof
relies on. Consequently:

- `meta.json axioms = []`, `deep_model_references = []`.
- `axiom_check.py` (G-AX) is a `status=skip` stub: there is no axiom or
  deep-model reference to validate against a real callee.

### 3.1 The two changed sites and why only one is observable

- **Site 1 — registration (`contribute_to_class`).** Pre-patch the handler is
  attached for every concrete model; post-patch it is attached only when a
  companion dimension field is declared. This is the behaviour the F2P test
  `test_post_init_not_connected` observes (a model with no companion field must
  have no receiver registered for its class). `registerInitHandler`'s
  postcondition `out = shouldRegister …` pins exactly this. Confirmed by a
  whole-tree search: this `contribute_to_class` is the *only* site in Django
  that connects `post_init` for image-field models, and no `super()` in the
  chain (`FileField.contribute_to_class`, `Field.contribute_to_class`) connects
  any signal — so the modeled decision is the complete registration behaviour.

- **Site 2 — the synchronization pass (`update_dimension_fields`).** The patch
  removes the leading `has_dimension_fields` early-return guard. This is
  **behaviour-preserving**: when no companion field is declared, the two final
  assignments are each already guarded by `if self.width_field` /
  `if self.height_field`, so the pass writes nothing whether or not the removed
  guard runs. `dimUpdate` encodes the post-patch logic (no leading guard) and
  yields `writeWidth = hasWidthField && proceed`, `writeHeight = hasHeightField
  && proceed`; with `hasWidthField = hasHeightField = false` both writes are
  `false` regardless of `proceed`. Hence site 2 has **no independently
  observable fixed behaviour** — it is a coupled refactor that keeps the
  removed-guard configuration a no-op, which is why there is a single
  `Solution_prepatch.lean` (failing on site 1).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`16801`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `shouldRegister` and `dimUpdate` to Python (pure R/I ops; no
A-tagged callee) and checks them against the behaviour of the patched
`ImageField.contribute_to_class` / `update_dimension_fields` driven over a
fuzzed grid of model/instance configurations.
