# mapping.md — django__django-15380

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 71e7c8e73712419626f1c2b6ec036e8559a2d667`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of each deep model.

Repo file under change: `django/db/migrations/autodetector.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `frameRenamedField` | `MigrationAutodetector.generate_renamed_fields` — `django/db/migrations/autodetector.py:822` (the per-field-key state-resolution prologue, body lines 825–827) | the modeled changed function: resolving the prior- and current-state model entries a candidate-renamed field acts on |
| `lookupState` *(deep model — A-reference)* | the `[app_label, name]` subscription of a `ProjectState.models` map (`self.from_state.models[...]`, `self.to_state.models[...]`; the map is built in `ProjectState.add_model`, `django/db/migrations/state.py:109`) | pure spec: resolving the model entry stored under a `(app_label, model_name)` key in a name-keyed state map |
| `renameLookup` *(deep model — A-reference)* | `self.renamed_models.get((app_label, model_name), model_name)` — `autodetector.py:825` (record populated at `autodetector.py:507`) | pure spec: a model's prior name from the rename record, or its current name when not renamed |
| `ModelEntry` | a `ModelState` value of `ProjectState.models` (`django/db/migrations/state.py`) | only the entry's identity (its `name`) is observed; the routine selects *which* entry to read |

The `model_name` the routine iterates is a **current** (`to_state`) model name —
`new_field_keys` is built from `self.to_state.models[app_label, model_name].fields`
(`autodetector.py:221-224`), so its keys carry current model names.
`old_model_name = self.renamed_models.get((app_label, model_name), model_name)`
is the model's **prior** name (its rename source, or its current name when not
renamed). This is the discriminator the whole bundle pins.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `(app_label, model_name)` dict key (both `str`, model name lower-cased) | `String × String` | tuple ↔ pair; component string equality ↔ `keyEq` |
| `ProjectState.models : {(str,str): ModelState}` | `List ((String × String) × ModelEntry)` (association list) | a Python dict ↔ a key/value assoc list; `d[k]` present ↔ `lookupState` returns `some`; `KeyError` (key absent) ↔ `lookupState` returns `none`. The order of the assoc list is immaterial: keys are unique, so `find?` and `dict.__getitem__` agree. |
| `self.renamed_models : {(str,str): str}` | `List ((String × String) × String)` | dict ↔ assoc list; `d.get(k, k[1])` ↔ `renameLookup` (`some` value, else the key's model-name component `k.2`) |
| a `ModelState` (the dict value) | `ModelEntry` (records `name`) | only the entry identity is observed — the routine decides *which* `ModelState` to read; downstream `.get_field(...)` reads are an R-identity not modeled here |

A model whose name changed is stored in `to_state.models` under its **new** key
(`add_model` keys by the state's own `(app_label, name_lower)`), and is **absent**
under its prior key — so `lookupState currentModels (app, priorName)` returns
`none` (the repository's `KeyError`) exactly when `priorName ≠ curModelName`,
which is precisely the renamed-model case the issue reports.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `lookupState` / `renameLookup` deep models ↔ the real state maps (A-reference)
There is **no consumed axiom**. The two foreign computations the routine performs
— a name-keyed lookup into a `ProjectState.models` dict, and a `dict.get` with a
fallback into `renamed_models` — are modeled **deeply** by `lookupState` and
`renameLookup` in the `pure` region. The patch does not change these primitives;
it changes *which key* the current-state lookup is given. G-AX validates the deep
models against the real Python primitives:

- `lookupState m key == m.get(key)` (presence ↔ `some`, absence ↔ `none`) over
  populated and missing keys;
- `renameLookup r key == r.get(key, key[1])` over present and absent rename
  records;
- and — the behavioural crux — that a `ProjectState` holding a renamed model
  keys the model under its **current** name and raises `KeyError` under its prior
  name, so the gold key selection (`to_state.models[app_label, model_name]`)
  succeeds while the pre-patch key selection
  (`to_state.models[app_label, old_model_name]`) raises, exactly when a model was
  renamed.

**Soundness check (G-AX):** `axiom_check.py` builds real `ProjectState`s (DB-free,
as the F2P test does) and a real `MigrationAutodetector`, populates a real
`renamed_models`, and asserts the three equalities above over boundary cases
(renamed model, un-renamed model, absent field) plus randomized app/name/rename
fuzz. Imports only the standard library + the in-image Django. Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`15380`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`renameLookup`/`lookupState` and the `do`-block's two-key resolution to Python
over real dict carriers, and compares against the patched repo behaviour: the
prior/current `ModelState` pair the gold-patched `generate_renamed_fields`
resolves for each new field key (observed by driving the REAL autodetector over
in-memory `ProjectState`s, exactly as the F2P `get_changes` helper does).
