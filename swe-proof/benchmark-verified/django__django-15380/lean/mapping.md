# mapping.md — symbol binding & type bijection (django__django-15380)

## Modeled function
- **Lean** `implementation_resolveFieldModels : List (ModelKey × String) →
  List (ModelKey × ModelState) → List (ModelKey × ModelState) →
  List (String × String × String) →
  List (Option ModelState × Option ModelState)`
- **Python** `MigrationAutodetector.generate_renamed_fields(self)` —
  `django/db/migrations/autodetector.py:821-828 @ base_commit`
  (`base_commit = 71e7c8e73712419626f1c2b6ec036e8559a2d667`).

The loop head, per candidate field key, locates the owning-model state in both
snapshots:

```python
for app_label, model_name, field_name in sorted(self.new_field_keys - self.old_field_keys):
    old_model_name = self.renamed_models.get((app_label, model_name), model_name)
    old_model_state = self.from_state.models[app_label, old_model_name]
    new_model_state = self.to_state.models[app_label, old_model_name]   # base (buggy)
    new_model_state = self.to_state.models[app_label, model_name]       # patched
    field = new_model_state.get_field(field_name)
    ...
```

The observable defect: when a model is renamed AND one of its fields renamed in
the same `makemigrations` step, `(app_label, model_name)` is in
`renamed_models`, so `old_model_name` is the PRIOR model name. The current
snapshot `to_state.models` is keyed by the CURRENT name, so indexing it by
`old_model_name` raises `KeyError: ('test_one', 'mymodel')` (the crash in the
issue traceback at line 823). Indexing by `model_name` (current name) locates
the model. Regression from aa4acc164d1247c0de515c959f7b09648b57dc42.

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| `(app_label, model_name)` key (lowercased names) | `ModelKey = String × String` | snapshot/rename-map key |
| `self.renamed_models` : `dict[(app,name) -> prior_name]` | `renameMap : List (ModelKey × String)` | current key → prior model name |
| `self.from_state.models` : `dict[(app,name) -> ModelState]` | `priorStates : List (ModelKey × ModelState)` | PRIOR snapshot, keyed by prior name |
| `self.to_state.models` : `dict[(app,name) -> ModelState]` | `currentStates : List (ModelKey × ModelState)` | CURRENT snapshot, keyed by current name |
| `sorted(self.new_field_keys - self.old_field_keys)` element `(app,name,field)` | `entries : List (String × String × String)` | candidate field keys, supplied in iteration order |
| `ModelState` (only `.name`, `.fields` touched) | `structure ModelState (name : String) (fields : List String)` | minimal touched surface; bijection here |
| located `(old_model_state, new_model_state)` per entry | `(Option ModelState × Option ModelState)` | `Option` totalizes the dict subscript; a real run reaches the line only with a present key |

`dict.get(k, default)` ↔ `List.lookup k l |>.getD default`.
`dict[k]` (subscript) ↔ `List.lookup k l` (modeled as a total `Option`; the
fix's entire content is WHICH key is used, not subscript-vs-get).

`ModelState.name` keys are stored lowercased by the model-state machinery
(`name_lower`); the rename map and snapshots use the lowercased `(app, name)`
pairs (see `renamed_models[app_label, model_name] = rem_model_name` at
autodetector.py:507 and `new_field_keys`/`old_field_keys` construction at
lines 213-224). G-CONF fuzzes lowercased identifier strings accordingly.

## Callee provenance
- `dict.get` / `dict.__getitem__` (the rename-map translation + the two snapshot
  indexings) — Python builtins; reproduced concretely as `List.lookup`/`.getD`
  (I-tagged), so no `opaque`/axiom is needed.
- `ModelState.get_field(field_name)` and the downstream rename-scan
  (`deep_deconstruct`, `questioner.ask_rename`, `add_operation`) are UNCHANGED by
  the fix and lie outside the modeled behavior (the fix is purely WHICH key
  indexes the current snapshot). They are not modeled and not axiomatized.
- No UNCHANGED callee property is consumed: the axioms region is empty; G-AX is a
  skip stub.

## Flag dependency
None. The fix is unconditional (a fixed index change). The only conditioning is
whether `(app_label, model_name)` is present in `renamed_models` (model renamed
this step), which determines whether `priorName ≠ modelName`. G-CONF fuzzes both
the renamed and not-renamed cases.

## G-CONF fuzz seed
`SEED = 15380` (pinned; used by conformance_check.py).
