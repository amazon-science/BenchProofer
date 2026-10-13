# refinement.md — django__django-7530

Operation correspondence between `implementation_consistency_pairs`
(Solution.lean) and the gold `patch.diff`. Tags: **R** (type refinement),
**A-consumed** (proof uses an axiom's property), **A-reference** (deep model
validated == real callee by G-AX), **I** (identical concrete op).

## Modeled function: the `(app_label, model_name)` enumeration

The post-patch generator is

```python
router.allow_migrate(connection.alias, app_label, model_name=model._meta.object_name)
for app_label in consistency_check_labels
for model in apps.get_app_config(app_label).get_models()
```

The behaviorally relevant content is the **sequence of `(app_label,
model_name)` pairs** the generator produces. `router.allow_migrate(...)` and the
enclosing `any(...)` consume those pairs; `connection.alias` is a per-call
constant identical on both versions. The fix changes only the *inner iterable*,
hence only which pairs are produced.

| # | `implementation_consistency_pairs` op | `patch.diff` counterpart | tag | justification |
|---|---|---|---|---|
| 1 | input `apps : List App` (each `App` = `{label, models}`) | the applications iterated by `for app_label in consistency_check_labels`, each carrying its OWN models via `apps.get_app_config(app_label).get_models()` | R | Python `AppConfig` ↔ Lean `App`, taking only the touched fields `label` and the owned-model-name list (see mapping.md). |
| 2 | `for a in apps do …` (outer accumulator loop) | `for app_label in consistency_check_labels` | I | ordered iteration over the applications — identical concrete control flow. |
| 3 | `for m in a.models do …` (inner loop over the app's OWN models) | `for model in apps.get_app_config(app_label).get_models()` — the application's own models | R / A-reference | the post-patch inner iterable IS "the models this application owns". Modeled DEEPLY as `a.models` (the app's own model names), not axiomatized. G-AX validates that the real `apps.get_app_config(label).get_models()` attributes each model only to the app that owns it; G-CONF confirms the loop's R/I behavior == `patch.diff`. |
| 4 | `acc := acc ++ [(a.label, m)]` then `return acc` | the produced argument tuple `(app_label, model_name)` for each `allow_migrate` call, in order | I | ordered construction of the `(label, model)` pairs — identical concrete operation. `connection.alias` (the constant first argument) is outside the modeled enumeration (mapping.md). |

No op in `implementation_consistency_pairs` is changed-inexpressible: the whole
enumeration is modeled deeply over the applications carrier. There is **no
consumed axiom** and **no opaque callee** (the `axioms` region is empty), so the
proof discharges purely by induction on the application list (front-recursive
per-application fold vs. the nested accumulator loop, PROOF_PLAYBOOK Route B).

## Pre-patch (the bug) — Solution_prepatch.lean

The pre-patch impl mirrors `apps.get_models(app_label)`: because `get_models`'s
first positional parameter is `include_auto_created` (not a label), the
`app_label` argument is ignored and the call returns **every model in the whole
project**. The buggy skeleton therefore first gathers `allModels` (the union of
all applications' models) and pairs **each** application label with **all** of
them — the cross-product. On any project with ≥2 applications owning distinct
models, this produces `(label, model)` pairs where the model does not belong to
the labeled application, so it disagrees with `pairsSpec` and
`correct_consistency_pairs` is unclosable (G-DIFF). This is the single
independently-observable fixed behavior, hence one prepatch variant.

## patch.diff

Gold verbatim (one-line inner-iterable change). Applies at `base_commit`; makes
the harness `resolved` (G-RESOLVE).
