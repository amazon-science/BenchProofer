# refinement.md — django__django-7530

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `appModelPairs` `do` block plus the deep `appPairs`/`allPairs` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement;
state the bijection), **A-consumed** (proof uses an axiom's `ensures`),
**A-reference** (a deep model validated == its real callee by G-AX), or **I**
(identical concrete op). EVERY step is R, A, or I.

This bundle has **no A-tagged step**: there is no consumed axiom and no `:|`
stub. The R/I legs are mechanically refuted by **G-CONF**
(`conformance_check.py`, §4.1); the narrative is audited by **G-EQ**.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## Gold hunk (`django/core/management/commands/makemigrations.py:104-109`)

```
  router.allow_migrate(connection.alias, app_label, model_name=model._meta.object_name)
  for app_label in consistency_check_labels
- for model in apps.get_models(app_label)
+ for model in apps.get_app_config(app_label).get_models()
```

The single-line change selects which models are enumerated *per application
label*: from `apps.get_models(app_label)` — `Apps.get_models`, which takes no
`app_label` and so binds it to the `include_auto_created` flag, returning the
**whole-project** model union for every label — to
`apps.get_app_config(app_label).get_models()` — that **application's own** models.

| # | Solution.lean impl op (`appModelPairs`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | parameter `apps : List AppEntry` | the application registry (the scanned `consistency_check_labels` with each `AppConfig`'s owned models) | R | registry ↔ `List (Nat × List Nat)` (mapping.md §2); a set of labels is materialized as a list, order immaterial (§2.1). Read-only; not `mut` (directive 5). |
| 2 | `appPairs a = a.2.map (fun m => (a.1, m))` | `(app_label, model) for model in apps.get_app_config(app_label).get_models()` (patched inner loop) | R + I | each application's label paired with **its own** models. The `map` is the inner generator; `a.2` is `get_app_config(app_label).get_models()` under the bijection (mapping.md §2, §3). Concrete, transliterated by G-CONF. |
| 3 | `allPairs apps` = the backward `while` fold concatenating `appPairs` over the registry | the full double generator `for app_label … for model …` | I | the outer loop over labels; front-recursive `allPairs` ⇔ left-to-right pair generation. The fold ops (`appPairs a`, `++`, the loop) are concrete, transliterated and diff-tested by G-CONF (multiset comparison, §2.1). |
| 4 | `out` returned (`List (Nat × Nat)`) | the pair stream consumed by `any(router.allow_migrate(connection.alias, app_label, model_name=model._meta.object_name) for …)` | R | `connection.alias` is constant within one scan and elided; `model._meta.object_name` is the model's observable identity ↔ the model `Nat`. The F2P test inspects these pairs as an unordered collection (mapping.md §2.1). |

## Discriminating content of the change

The fix vs. the bug differs exactly on **which models pair with which label**:
the fix pairs label `L` with `L`'s OWN models (`appPairs`), the bug pairs every
label with the WHOLE-registry model union. The frozen postcondition
`out = allPairs apps` (each label × its own models) pins the fix.
`Solution_prepatch.lean` reproduces the bug — every label paired with the global
model union (`(apps.map (·.2)).flatten`) — and **fails** `out = allPairs apps`
(G-DIFF) precisely on registries where some app's own model set ≠ the global
union (i.e. more than one distinct owned-model set: the issue's sharding
scenario). G-CONF additionally asserts the model never matches the bug on such
discriminating registries.

## No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — the per-label
model selection — is modeled **deeply** (`appPairs`/`allPairs`, steps 2-3, R/I),
not hidden behind an axiom about the function under change. There is **no
consumed axiom** and **no deep-model A-reference** (no unchanged callee is
deeply modeled and G-AX-validated): the registry's per-app/whole-project model
data is reproduced from real Django source directly inside the G-CONF oracle, so
the refinement audit is fully mechanical (G-CONF), not axiomatic (G-AX skips).

## verify(Solution) ⇒ resolved

`appModelPairs` verifies only if its output equals the exact per-application
own-model expansion `allPairs apps` (step 3). By R (registry ↔ `List AppEntry`,
label/model ↔ `Nat`, alias elided) the verified enumeration equals the patched
generator's `(app_label, model)` stream up to the order-insensitivity the F2P
test tolerates (mapping.md §2.1). By G-CONF the R/I transliteration of the fold
agrees with `patch.diff`'s behaviour on ≥10⁵ fuzzed registries and diverges from
the pre-patch bug exactly where the fix does. Therefore a model satisfying this
spec, refined by the map above, is the gold patch up to type refinement — and
the gold patch resolves (G-RESOLVE). The single trust point is refinement
fidelity (this doc + G-CONF); there is no axiom-soundness trust point (no G-AX).
