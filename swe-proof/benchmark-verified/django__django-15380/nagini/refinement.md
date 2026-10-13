# refinement.md — django__django-15380

The operation-by-operation correspondence between `model.py`'s implementation
(`resolve_field_states`, plus the deep `prior_name` helper) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement), **A** (split into
**A-consumed** / **A-reference**), or **I** (identical concrete operation). The
claim: *any implementation that verifies against this frozen spec, refined per
the map below, is behaviourally equal to the gold patch on the tested inputs,
so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The patched site — `generate_renamed_fields()` (`django/db/migrations/autodetector.py:821`)

Gold hunk (body of the per-field loop at lines 824-828):
```
  old_model_name = self.renamed_models.get((app_label, model_name), model_name)
  old_model_state = self.from_state.models[app_label, old_model_name]
- new_model_state = self.to_state.models[app_label, old_model_name]
+ new_model_state = self.to_state.models[app_label, model_name]
  field = new_model_state.get_field(field_name)
```

The loop iterates `(app_label, model_name, field_name) ∈ new_field_keys -
old_field_keys`. `model_name` is the model's **later-state** name; `field_name`
was enumerated from `to_state.models[app_label, model_name].fields`
(autodetector.py:221-225). `from_state.models` is keyed by **prior-state** model
names, `to_state.models` by **later-state** names (autodetector.py:213-225). The
canonical correct pattern at autodetector.py:946-949 does exactly the two-key
lookup this patch restores: prior state by `renamed_models.get(...)`, later
state by the bare `model_name`.

| # | model.py impl op (`resolve_field_states`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `from_state: Dict[int, int]`, `to_state: Dict[int, int]` | `self.from_state.models`, `self.to_state.models` (`StateApps` model registries) | R | each registry is a mapping `name -> ModelState`; the `(app_label, model_name)` tuple key is abstracted to a single `int` model-name token (one app fixed; the bug is in the model-name component), and the `ModelState` value to an `int` descriptor token. The field then read off the descriptor (`get_field`) is enumerated from that very descriptor, so the descriptor identity is all the spec needs. (mapping.md §2.) |
| A2 | `renamed: Dict[int, int]` | `self.renamed_models` | R | mapping `(app_label, later_name) -> prior_name`, abstracted to `later_name -> prior_name` (int→int). (mapping.md §2.) |
| A3 | `old_name = prior_name(correspondence, later)` (the `@Pure` helper: `correspondence[later]` if `later in correspondence` else `later`) | `old_model_name = self.renamed_models.get((app_label, model_name), model_name)` | I + R | `dict.get(k, default)` is exactly "`m[k]` if `k in m` else `default`"; `prior_name` spells out that total fallback lookup. Concrete control flow identical; only the key/value carrier is refined (R). |
| A4 | `old_descriptor = prior_registry[old_name]` | `old_model_state = self.from_state.models[app_label, old_model_name]` | I + R | the prior-state lookup, **unchanged** by the patch, keyed by the prior name. Identical concrete subscription under the registry refinement. |
| A5 | `new_descriptor = later_registry[later]` | `new_model_state = self.to_state.models[app_label, model_name]` (the **+** line) | I + R | the later-state lookup keyed by the model's **later** name `later`/`model_name` — the one operation the patch corrects. Identical concrete subscription under the registry refinement. |
| A6 | (no node) | `field = new_model_state.get_field(field_name)` | R | `get_field(field_name)` is `new_model_state.fields[field_name]` (state.py:687-690), which succeeds because `field_name` was enumerated from `new_model_state.fields`. Not the operation under change; the descriptor token returned by A5 is the object it is read from, so the model stops at the descriptor (mapping.md §3). |

The discriminating content of the change lives in step **A5**: the later
descriptor is keyed by `later` (the new name), not by `old_name` (the prior
name). The pre-patch code used `old_name`; `model_prepatch.py` reproduces that
(`later_registry[old_name]`) and **fails** verification because the spec only
guarantees `old_name in prior_registry` (precondition
`prior_name(correspondence, later) in prior_registry`) — it does NOT guarantee
`old_name in later_registry`. The unprovable access precondition
`later_registry[old_name]` is exactly the `KeyError` the issue
reports: when a model is renamed (`old_name != later`), the later-state registry
holds it only under `later`, so indexing it by `old_name` is a missing key
(G-DIFF).

## B. Consumed axiom vs. deep-model reference

- **No consumed axiom (no `@ContractOnly`).** The behaviour under change — which
  name keys the later-state registry — is modelled **deeply** (`prior_name` +
  the two guarded subscriptions in `resolve_field_states`). There is no axiom
  the proof consumes.
- **A-reference (G-AX).** The two registry subscriptions are ordinary mapping
  lookups; `dict.get` / `dict[...]` semantics are validated against real Python
  by `axiom_check.py` (G-AX): for renamed models the prior name is absent from
  the later-state registry (so the pre-patch key raises) while the later name is
  present (so the fixed key succeeds), and for unchanged names both keys
  coincide. This is a reference check of the model's lookup discipline against
  Python's dict semantics, not a consumed axiom.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the later-state registry's lookup key — is a concrete dict
subscription, modelled directly (I + R, step A5), not hidden behind an axiom
about the function under change. There is no consumed `@ContractOnly`.

## D. verify(model) ⇒ resolved

`resolve_field_states` verifies only if the later descriptor is obtained by
indexing the later-state registry with the model's **later** name `later` (A5;
any other key — in particular the prior name — leaves the `later_registry[...]`
access precondition unprovable, as `model_prepatch.py` shows) and the prior descriptor
by the prior name (A4). By R (tuple key → int token, `ModelState` → descriptor
token, `dict.get` ↔ `prior_name`) the verified selection equals the gold patch's
`old_model_state = from_state[app_label, old_model_name]` /
`new_model_state = to_state[app_label, model_name]` on the tested inputs; A-ref
(G-AX) confirms the dict semantics. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement — and the gold
patch resolves (G-RESOLVE: the F2P `test_rename_field_with_renamed_model` now
detects the simultaneous model+field rename instead of crashing). The trust
points are exactly the two of PLAN §1.1: axiom soundness (here only the A-ref
dict-semantics check, G-AX) and refinement fidelity (this document, G-EQ).
