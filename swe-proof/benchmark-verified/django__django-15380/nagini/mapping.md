# mapping.md — django__django-15380

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 71e7c8e73712419626f1c2b6ec036e8559a2d667`, states the type
abstraction, and gives the provenance of the (sole) A-reference callee check.

Repo file under change: `django/db/migrations/autodetector.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `resolve_field_states(prior_registry, later_registry, correspondence, later)` | the per-field body of `MigrationAutodetector.generate_renamed_fields()` — `django/db/migrations/autodetector.py:821` (loop body, lines 825-828) | the modeled changed function: selection of the prior/later model descriptors used to fetch the field being checked for a rename |
| `prior_registry: Dict[int, int]` | `self.from_state.models` — `autodetector.py:32` (assigned), keyed by prior model names; built/keyed at `autodetector.py:213-219` | prior-state model registry: model-name token → descriptor token |
| `later_registry: Dict[int, int]` | `self.to_state.models` — `autodetector.py:33` (assigned), keyed by later model names; built/keyed at `autodetector.py:221-225` | later-state model registry: model-name token → descriptor token |
| `correspondence: Dict[int, int]` | `self.renamed_models` — `autodetector.py:472` (init), populated `autodetector.py:507` | name-correspondence map: later-state model-name token → prior-state model-name token |
| `prior_name(correspondence, later)` | `self.renamed_models.get((app_label, model_name), model_name)` — `autodetector.py:825` | pure spec: the model's prior-state name (the map with a fallback to the later name) |
| `Result()[0]` (prior descriptor) | `old_model_state = self.from_state.models[app_label, old_model_name]` — `autodetector.py:826` | prior model descriptor (unchanged lookup) |
| `Result()[1]` (later descriptor) | `new_model_state = self.to_state.models[app_label, model_name]` — `autodetector.py:827` **post-patch** (pre-patch: `... old_model_name`) | later model descriptor (the corrected lookup) |

The patched line (`autodetector.py:827`) changes the later-state registry key
from `old_model_name` to `model_name`. The field then read,
`new_model_state.get_field(field_name)` (`autodetector.py:828`), is
`new_model_state.fields[field_name]` (`django/db/migrations/state.py:687-690`);
`field_name` was enumerated from exactly that descriptor's fields
(`autodetector.py:221-225`), so once the correct descriptor is selected the
field read always succeeds — it is not modelled (the descriptor token is the
object it is read from).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `StateApps.models`, a `dict` keyed by `(app_label, model_name)` → `ModelState` | `Dict[int, int]` | one app fixed (the bug is purely in the model-name component); the `(app_label, model_name)` tuple key is abstracted to a single `int` model-name token, the `ModelState` value to an `int` descriptor token. `d[k]` ↔ registry subscription; `k in d` ↔ membership. |
| `self.renamed_models`, a `dict` keyed by `(app_label, later_name)` → `prior_name` | `Dict[int, int]` | tuple key abstracted to the later-name `int` token; value is the prior-name `int` token. |
| `dict.get((app_label, model_name), model_name)` | `prior_name(correspondence, later)` = `correspondence[later] if later in correspondence else later` | `dict.get(k, default)` ≡ guarded lookup with total fallback. |
| `ModelState` object (`new_model_state` / `old_model_state`) | an `int` descriptor token | the spec needs only descriptor identity; `get_field` off it is not the changed op and always succeeds for the enumerated `field_name`. |

Dict subscription is guarded by an explicit `k in d` test (`prior_name`) and by
the membership preconditions (`later in later_registry`,
`prior_name(correspondence, later) in prior_registry`), which mirror the repo
invariant: `model_name ∈ to_state.models` (the field was enumerated there) and
`old_model_name ∈ from_state.models` (the prior name is where the prior state
holds the model).

## 3. A-reference provenance (checked by G-AX / axiom_check.py)

There is **no consumed `@ContractOnly` axiom**. The behaviour under change is the
choice of registry key, modelled deeply. The only out-of-band check is an
**A-reference**: that the model's lookup discipline matches real Python `dict`
semantics, on the exact configuration the bug concerns.

**Real callees:** Python `dict.get(key, default)` and `dict[key]` /
`key in dict` on the `from_state.models` / `to_state.models` /
`renamed_models` registries. Behaviour (CPython, every supported 3.x):
- `dict.get((app_label, model_name), model_name)` returns the recorded prior
  name when the model was renamed, else the bare `model_name`.
- `from_state.models` is keyed by prior names: `(app_label, old_model_name)` is a
  key (`autodetector.py:213-219` enumerates `old_field_keys` through exactly
  this lookup).
- `to_state.models` is keyed by later names: `(app_label, model_name)` is a key,
  but for a renamed model `(app_label, old_model_name)` is **not** — so the
  pre-patch `to_state.models[app_label, old_model_name]` raises `KeyError`
  (the traceback in the issue: `KeyError: ('test_one', 'mymodel')`), while the
  post-patch `to_state.models[app_label, model_name]` succeeds.
- When the model is not renamed, `old_model_name == model_name`, so both keys
  coincide and either lookup succeeds (the regression only manifests when a
  model and one of its fields are renamed in one step).

**Soundness check (G-AX):** `axiom_check.py` constructs prior/later registries
and a rename map directly in Python (stdlib only) and asserts, over boundary +
randomized fuzz: (a) `prior_name`'s model definition equals `dict.get` with the
fallback; (b) for renamed models the prior name is absent from the later
registry (so the pre-patch key raises `KeyError`) while the later name is
present (post-patch key succeeds); (c) for unchanged names both keys coincide
and the selected descriptors equal `from_state[name]` / `to_state[name]`. It
imports nothing repo-specific. Exit 0 iff sound.
