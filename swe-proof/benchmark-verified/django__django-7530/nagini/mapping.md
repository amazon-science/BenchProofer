# mapping.md — django__django-7530

Binds every `model.py` symbol to its repository counterpart at
`base_commit = f8fab6f90233c7114d642dfe01a4e6d4cb14ee7d`, states the type
abstraction, and gives the provenance of the deep-model reference (the registry
callee the gold patch switches to).

Repo file under change:
`django/core/management/commands/makemigrations.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `members_for_group(owner, member, target)` | the inner generator `for model in apps.get_models(app_label)` inside the `any(...)` history-consistency pre-check of `Command.handle` — `django/core/management/commands/makemigrations.py:104-109` (the iteration that supplies the `(app_label, model)` pairs to `router.allow_migrate`) | the modeled changed iteration: the per-app set of models to consult the router about |
| `gathered(owner, member, target)` *(deep model — A-reference)* | `AppConfig.get_models()` — `django/apps/config.py:174-194`, reached via `apps.get_app_config(app_label).get_models()` (`django/apps/registry.py:141` + `config.py:174`) post-patch | pure spec: the models belonging to one app, in registry order; the deep model of the fixed callee, validated `gathered == AppConfig.get_models()` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `owner` (parameter) | the app-ownership of each model in the project registry: model at registry position `k` belongs to app `owner[k]`. Source of truth: `AppConfig.models` per app, and the project-wide flattening in `Apps.get_models` (`registry.py:160-178`) | pure spec: registry ownership stream |
| `member` (parameter) | the model identity at each registry position (`model._meta.object_name`, used as the `model_name=` argument to `router.allow_migrate`) | pure spec: registry member-identity stream |
| `target` (parameter) | `app_label`, the outer-loop variable `for app_label in consistency_check_labels` (`makemigrations.py:107`) | the app whose consistency is being checked |

The pre-patch repo symbol the change removes (for the refinement audit, not
referenced from the consumer spec view): `apps.get_models(app_label)`
(`Apps.get_models`, `django/apps/registry.py:160`). Its signature is
`get_models(self, include_auto_created=False, include_swapped=False)`: it takes
NO `app_label` parameter, so the positional `app_label` is bound to
`include_auto_created` and the call returns the PROJECT-WIDE model list
(flattened over `self.app_configs.values()`), ignoring the intended app filter.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the project's registered models, in iteration order, each tagged with its owning app | two aligned `List[int]` streams `owner` / `member` (`len(owner) == len(member)`) | registry position `k` ↔ index `k`; `owner[k]` ↔ the app id of the k-th model (`model._meta.app_label` interned to an int); `member[k]` ↔ the model's identity (`model._meta.object_name` interned to an int) |
| an `app_label` (a `str` app label) | `int` group id (`target`) | distinct app labels ↔ distinct ints (the only relation the spec needs is equality of app ids) |
| a model object `model` | `int` member id (`member[k]`) | the spec only needs model identity and which app owns it; both are ints |
| the iterable returned by the inner `for model in ...` | `List[int]` of member ids (the function result) | the gathered members, in registry order |
| the surrounding double comprehension + `router.allow_migrate(... app_label ... model ...)` + `any(...)` + `check_consistent_history` | not modeled (unchanged control flow around the changed iteration) | the gold change is ONLY the inner iterable; the router call, the `any`, and the consistency check are identical pre/post-patch. The model isolates the one changed sub-expression: which models are paired with `app_label`. |

Models are identified by interned `int`s (Nagini bans `str` indexing and rich
objects); the specification is carried over `PSeq[int]` via `ToSeq`. The two
parallel streams encode the registry's ground-truth ownership: every model has
exactly one owning app.

## 3. Deep-model reference (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `gathered` deep model ↔ `AppConfig.get_models()` (A-reference)
**Callee:** `django.apps.config.AppConfig.get_models(include_auto_created=False,
include_swapped=False)` (`django/apps/config.py:174-194`), reached post-patch via
`apps.get_app_config(app_label).get_models()`. `get_app_config(app_label)`
(`registry.py:141-156`) returns the single `AppConfig` whose label is
`app_label`; that config's `get_models()` yields the models in `self.models`
(the models declared in THAT app), filtered for auto-created/swapped:

```python
def get_models(self, include_auto_created=False, include_swapped=False):
    self.apps.check_models_ready()
    for model in self.models.values():
        if model._meta.auto_created and not include_auto_created:
            continue
        if model._meta.swapped and not include_swapped:
            continue
        yield model
```

So `apps.get_app_config(app_label).get_models()` yields EXACTLY the (non-auto,
non-swapped) models whose owning app is `app_label`, in that app's registration
order. This is precisely the deep model

  `gathered(owner, member, target)` = the members `member[k]` (in registry
  order) for which `owner[k] == target`,

under the type bijection of §2 (registry order restricted to one app preserves
relative order; ownership `owner[k] == target` ↔ "model in `app_label`'s
`AppConfig.models`"). The auto-created/swapped filter is orthogonal to the
change (both callees apply the same default filter); it only narrows WHICH
models exist in the registry streams, never their ownership, so it does not
affect the ownership property the spec pins.

**Flag dependency:** both the fixed and the pre-patch callees use the default
`include_auto_created=False, include_swapped=False`. (The pre-patch bug is
exactly that the positional `app_label` was being bound to
`include_auto_created` — but Django app labels are non-empty strings, hence
truthy, so the buggy call effectively ran `get_models(include_auto_created=True)`
project-wide; the auto-created models that adds are a side effect of the bug, not
of the modeled per-app ownership property. The model pins the ownership
property, which is what the F2P test checks via
`get_app_config(app).get_model(model_name)`.)

**Soundness check (G-AX):** `axiom_check.py` synthesises a real two-app Django
registry with DISJOINT model sets, runs the real
`apps.get_app_config(label).get_models()`, and asserts it equals the deep model
`gathered(owner, member, label)` for every app — every returned model belongs to
the queried app (soundness) and none is omitted (completeness). It also
witnesses the pre-patch bug: `apps.get_models(label)` returns the project-wide
set (foreign-app models offered under `label`), differing from `gathered`
whenever another app owns a model. It imports only Django (the framework the
patched file lives in) and builds the apps in a temp dir; exit 0 iff sound.
Docs: https://docs.djangoproject.com/en/stable/ref/applications/#django.apps.config.AppConfig.get_models
and https://docs.djangoproject.com/en/stable/ref/applications/#django.apps.registry.Apps.get_models

## 4. Note on the F2P/P2P labels

The instance's `FAIL_TO_PASS` lists a `SquashMigrationsTests` name, an upstream
SWE-Bench-Verified labeling artifact; the gold patch + `test_patch` modify
`test_makemigrations_consistency_checks_respect_routers`
(`tests/migrations/test_commands.py`), which is the test that observes the
change. The modeled behaviour is faithful to the gold patch regardless of the
label string; G-RESOLVE runs the official harness on the gold `patch.diff`.
