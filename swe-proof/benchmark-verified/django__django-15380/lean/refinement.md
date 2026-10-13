# refinement.md — operation correspondence (django__django-15380)

Maps every op in `implementation_resolveFieldModels` to its `patch.diff`
counterpart. Tags: **R** type refinement · **A-consumed** proof uses axiom
property · **A-reference** deep model validated == real callee (G-AX) · **I**
identical concrete op.

The patched Python (`MigrationAutodetector.generate_renamed_fields`, the loop
head over `sorted(self.new_field_keys - self.old_field_keys)`) computes, per
candidate field key, the model's prior name via the rename map and then locates
the owning-model state in BOTH the prior (`from_state`) and current
(`to_state`) snapshots. The fix changes the index used for the CURRENT snapshot
from the prior name to the current name. We model the rename-map translation and
the two snapshot indexings deeply and concretely as total `List.lookup`s.

| # | Lean impl op | patch.diff / source counterpart | tag | justification |
|---|---|---|---|---|
| 1 | iterate `for entry in entries` | `for app_label, model_name, field_name in sorted(self.new_field_keys - self.old_field_keys)` | R | the candidate-key set (`new_field_keys − old_field_keys`, already sorted upstream) ↔ `entries : List (String × String × String)`. The sort/set-difference is upstream of the changed line and supplied as the input list; order preserved. |
| 2 | `appLabel := entry.1`, `modelName := entry.2.1` | unpack `app_label, model_name, field_name` | R | tuple ↔ tuple; the `field_name` component selects the field downstream (unchanged `get_field`, out of model scope) and is not consumed here. |
| 3 | `priorName := (renameMap.lookup (appLabel, modelName)).getD modelName` | `old_model_name = self.renamed_models.get((app_label, model_name), model_name)` | I | `dict.get(k, default)` ↔ `List.lookup` then `.getD default`. The rename map `(app_label, model_name) → prior name`. |
| 4 | `priorState := priorStates.lookup (appLabel, priorName)` | `old_model_state = self.from_state.models[app_label, old_model_name]` | I | snapshot indexing `from_state.models[(app_label, prior_name)]` ↔ `List.lookup`. UNCHANGED by the fix. (Total `Option` lookup refines the dict-subscript; a real run only reaches this with a present key.) |
| 5 | `currentState := currentStates.lookup (appLabel, modelName)` | `new_model_state = self.to_state.models[app_label, model_name]` (PATCHED line; base used `old_model_name`) | I | **the changed op**, modeled deeply: the current snapshot is indexed by the CURRENT name `model_name`, not the prior name. This is the entire fix. The base-commit bug used `old_model_name`, which misses a model renamed in this same step (→ `KeyError`). |
| 6 | `acc := acc ++ [(priorState, currentState)]`; `return acc` | the pair of located model states feeding `new_model_state.get_field(field_name)` and the rename scan | R | we observe the LOCATED owning-model states (the result of the two indexings). `get_field` and the downstream rename-scan are unchanged by the fix and out of model scope; pairing/append models the per-entry accumulation. |

No A-consumed rows: the proof discharges the `List.map`/`forIn` equality
directly; no UNCHANGED callee property is assumed (axioms region empty).

No A-reference rows: the three indexings (rows 3–5) are reproduced concretely as
total `List.lookup`s (I-tagged), not abstracted behind a model that needs G-AX
validation. No changed-inexpressible op.

The discriminating clause is **row 5**: the spec pins
`currentState = currentStates.lookup (appLabel, modelName)` (current name). The
prepatch impl uses `currentStates.lookup (appLabel, priorName)` (prior name);
whenever the model was renamed in this step (`priorName ≠ modelName`) and the
current snapshot has no entry under the prior name, the prepatch `currentState`
is `none` while the spec demands the located `some …`. Hence prepatch
`correct_resolveFieldModels` cannot close — the G-DIFF signal, and exactly the
crash the F2P test (`test_rename_field_with_renamed_model`) exercises.
