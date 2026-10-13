# mapping.md — django__django-7530

## Modeled function

The gold patch changes one expression inside `Command.handle` in
`makemigrations.py`: the inner generator of the consistency-check `any(...)`. The
modeled behavior is the **enumeration of `(app_label, model_name)` pairs** that
the consistency check feeds to `router.allow_migrate(connection.alias, app_label,
model_name=...)`. We model that enumeration as a pure function over the
applications carrier.

| Lean | Python | file:line @ base_commit `f8fab6f90233` |
|---|---|---|
| `implementation_consistency_pairs` / `problem_spec_consistency_pairs` / `correct_consistency_pairs` | the `(app_label, model)` enumeration driving `allow_migrate(...)` in the `any(...)` over `consistency_check_labels` | `django/core/management/commands/makemigrations.py:104-109` (post-patch inner: `for model in apps.get_app_config(app_label).get_models()`) |

## The change (bug ↔ fix)

```
  for app_label in consistency_check_labels
- for model in apps.get_models(app_label)                       # pre-patch
+ for model in apps.get_app_config(app_label).get_models()      # post-patch
```

* `Apps.get_models(self, include_auto_created=False, include_swapped=False)`
  (`django/apps/registry.py:160`) takes **no app-label argument**. The
  positional `app_label` is silently bound to `include_auto_created`, so the call
  returns **every model in the whole project** for *every* label. The outer
  `for app_label in consistency_check_labels` then produces the full
  cross-product: each application label paired with all project models —
  including models that belong to *other* applications. This is exactly the
  "invalid `(app_label, model)` combinations" the issue reports.
* `AppConfig.get_models(...)` (`django/apps/config.py:174`) yields only the models
  registered to **that one application** (modulo auto-created/swapped). So
  `apps.get_app_config(app_label).get_models()` enumerates only the models the
  application actually owns.

## Type bijection (Lean ↔ Python) — used by G-CONF + G-AX

| Python | Lean | notes |
|---|---|---|
| an installed application (its `AppConfig`) | `App` (a `structure` with `label : String`, `models : List String`) | only the touched fields: the app's label and the names of the models it owns |
| `app_config.label` | `App.label : String` | the application label fed to `allow_migrate` as `app_label` |
| `model._meta.object_name` for each owned model | an element of `App.models : List String` | the model name fed to `allow_migrate` as `model_name=...` |
| the list of installed applications (`apps.get_app_configs()` over `consistency_check_labels`) | `apps : List App` | application order preserved |
| the produced `(app_label, model_name)` pairs | `List (String × String)` | one pair per `allow_migrate` call argument tuple `(app_label, model_name)` |

The modeled enumeration deliberately drops the read-only context that does not
affect *which* pairs are produced: `connection.alias` (a constant prefix per
call, identical across both buggy and fixed versions), the `DATABASE_ROUTERS` /
engine guards (they gate *whether* the loop runs, not its pair contents), and the
`any(...)` short-circuit (a downstream consumer of the pairs). The bug is purely
in the *set/sequence of `(app_label, model_name)` pairs*, which is what the spec
pins.

## Callee provenance / flag deps

- The pair enumeration is modeled **deeply** from the applications carrier
  (`appPairs` / `pairsSpec`), not delegated to an opaque callee. The post-patch
  `AppConfig.get_models()` is, on the modeled domain, exactly "the models this
  application owns" — captured directly as `App.models`. Hence the `axioms`
  region declares no `opaque` and the proof needs no `_prop` axiom (G-AX = skip).
- The auto-created / swapped filtering inside `AppConfig.get_models` is outside
  the modeled domain: it filters *which* of the application's own models appear,
  not *which application a model is attributed to*. The bug being fixed is the
  attribution (pairing models with the wrong app), so `App.models` is taken to be
  the already-filtered set of the app's own visible models. Recorded here so G-AX
  fuzzes the attribution property, not the filtering.

## G-CONF fuzz seed

`conf_seed = 7530` (pinned; see conformance_check.py and meta.json).
