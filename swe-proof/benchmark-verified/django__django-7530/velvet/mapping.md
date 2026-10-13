# mapping.md — django__django-7530

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = f8fab6f90233c7114d642dfe01a4e6d4cb14ee7d`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and gives the
provenance of each modeled callee.

Repo file under change:
`django/core/management/commands/makemigrations.py` (the `handle` method).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `appModelPairs (apps : List AppEntry)` | the (app_label, model) generator expression inside `Command.handle` — `django/core/management/commands/makemigrations.py:104-109` (the `any(... for app_label in consistency_check_labels for model in ...)` whose pairs are passed to `router.allow_migrate`) | the modeled changed function: the enumeration of (label, model) pairs scanned for consistency |
| `AppEntry := Nat × List Nat` | one application registry entry: an `AppConfig` (its `label`) together with the models it owns | type carrier (R) |
| `appPairs (a : AppEntry)` | `(app_label, model) for model in apps.get_app_config(app_label).get_models()` — the patched inner generator, `makemigrations.py:108` post-patch | pure spec: the pairs one application contributes (its label × its OWN models) |
| `allPairs (apps : List AppEntry)` *(deep model — R/I)* | the full double generator: `for app_label in consistency_check_labels for model in apps.get_app_config(app_label).get_models()` | pure spec: in-order concatenation of every application's own pairs |

No axioms are consumed: the behaviour under specification (which (label, model)
pairs are enumerated) is modeled **deeply** over the registry carrier given as
input. The two registry callees the gold patch swaps between
(`Apps.get_models` ⇄ `AppConfig.get_models`) are **not** axiomatized — their
*data* (each app's own models, vs. the whole-project union) is reproduced
faithfully from the real Django source in `conformance_check.py` (G-CONF), which
is the authoritative refinement audit for this bundle.

### Pre-patch repo symbols (refinement audit only — not in the consumer view)
- `apps.get_models(app_label)` (`makemigrations.py:108` pre-patch) — `Apps.get_models`
  (`django/apps/registry.py:160`). Its signature is
  `get_models(self, include_auto_created=False, include_swapped=False)`: it takes
  **no** `app_label`. The pre-patch call therefore binds `app_label` to the
  `include_auto_created` positional flag and returns the **whole-project** model
  union (every app's models) for *every* label — the bug.
- `apps.get_app_config(app_label).get_models()` (`makemigrations.py:108` post-patch)
  — `Apps.get_app_config` (`registry.py:236`) returns the one `AppConfig`;
  `AppConfig.get_models` (`django/apps/config.py:174`) yields **only that
  application's own** models. The fix.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the real repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the application registry restricted to the scanned labels (`consistency_check_labels`, a `set` of `AppConfig.label`) | `List AppEntry = List (Nat × List Nat)` | each registered application ↔ one `(label, owned_models)` entry; an `AppConfig` ↔ its `label`; the app's own model classes ↔ the `List Nat` of model identifiers. The set is materialized as a list; order is immaterial to the observable (see §2.1). |
| an application's `label` (a `str`) | `Nat` (opaque identifier) | label string ↔ a distinct `Nat`; the proof performs no operation on it, only carries it into each pair. The G-CONF bijection assigns each distinct label/model a distinct id. |
| a model class (observed only via `model._meta.object_name`) | `Nat` (opaque identifier) | model ↔ a distinct `Nat`. The scan's observable per pair is `(connection.alias` fixed, `app_label`, `model._meta.object_name)`; alias is constant within one scan and elided, so the pair carrier is `(label, model)`. |
| `apps.get_app_config(app_label).get_models()` (patched inner loop) | `appPairs a = a.2.map (fun m => (a.1, m))` | the application's own models, each paired with its label. The `include_auto_created` / `include_swapped` filters of `AppConfig.get_models` are reproduced in the G-CONF shadow's `appconfig_get_models`; the default (both False) is what `handle` uses. |

### 2.1 Order / multiplicity
`consistency_check_labels` is a Python `set`, so the outer iteration order is
unspecified; the inner `get_models()` order is the app's registration order.
The pairs feed `any(router.allow_migrate(...) for ...)`, and the F2P test
inspects `allow_migrate.mock_calls` as an **unordered collection** (it asserts
membership / per-call validity, `assert_any_call`, not a fixed sequence).
Accordingly G-CONF compares pair collections as **multisets** (`Counter`) and
shuffles the label order each trial. `allPairs` fixes a concrete order (registry
order) — a sound representative of the set, since the observable is
order-insensitive.

## 3. Callee provenance — no axioms (deep R/I model)

There is **no `axiom`** and **no `:|` stub** in this bundle, hence **no G-AX**
(the gate skips when `axiom_check.py` is absent — `gates.py` `gate_ax`). The
operation the patch changes — which models are enumerated per application — is
modeled **deeply** as the per-application own-model expansion `appPairs`/`allPairs`
(the `pure` region) and built by the verified loop. The two registry methods the
patch swaps are reproduced faithfully from real Django source in
`conformance_check.py`:

- `AppConfig.get_models` (`django/apps/config.py:174`) → `appconfig_get_models`
  (skips `auto_created` / `swapped` models unless the flag is set).
- `Apps.get_models` (`django/apps/registry.py:160`) → `apps_get_models`
  (flat union over all app configs) — used to reproduce the **bug** so G-CONF
  can confirm the model tracks the **fix**, not the bug.

When a configured Django is importable, G-CONF additionally cross-checks the
real `apps.get_app_config(L).get_models()` vs `apps.get_models()` to confirm the
divergence the model captures is the real one (best-effort; never fails the gate).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`7530`** so the
consumer-side verdict is reproducible. It transliterates `appPairs`/`allPairs`
(R/I-tagged ops) to Python over the real registry carrier; there is no A-tagged
callee to leave as a real call (the proof consumes no axiom). It diffs the shadow
against the patched generator over ≥10⁵ fuzzed registries (boundary shapes first:
empty, single-app, disjoint-model shards, auto-created/swapped-only apps, falsy
label) and additionally asserts the shadow disagrees with the **buggy**
whole-project-union expansion exactly on the discriminating registries.
