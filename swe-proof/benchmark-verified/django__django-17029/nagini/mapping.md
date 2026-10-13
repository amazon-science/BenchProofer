# mapping.md — django__django-17029

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 953f29f700a60fc09b08b2c2270c12c447490c6a`, states the type
abstraction, and records callee provenance.

Repo file under change: `django/apps/registry.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `clear_all_caches(registry)` | `Apps.clear_cache(self)` — `django/apps/registry.py:370` (body 376-384) | the modeled changed function (the registry's cache-reset operation) |
| `Registry` (class) | `Apps` (class) — `django/apps/registry.py:13` | the registry instance whose memoizing methods are reset; modeled with only the touched state (the per-method cache occupancies) |
| `registry.models_cache_occupancy` | `Apps.get_models`'s `functools.cache` cache occupancy — i.e. `Apps.get_models.cache_info().currsize` (`get_models` defined at `django/apps/registry.py:168-169`, `@functools.cache`) | observable occupancy of the all-models lookup cache |
| `registry.swappable_cache_occupancy` | `Apps.get_swappable_settings_name`'s `functools.cache` cache occupancy — i.e. `Apps.get_swappable_settings_name.cache_info().currsize` (`get_swappable_settings_name` defined at `django/apps/registry.py:283-284`, `@functools.cache`) | observable occupancy of the swappable-settings-name lookup cache |

The two memoizing methods are exactly the two methods on `Apps` decorated with
`@functools.cache` (`functools.cache` == `functools.lru_cache(maxsize=None)`),
confirmed by `grep '@functools.cache'` over `django/apps/registry.py` at
base_commit: lines 168 (`get_models`) and 283 (`get_swappable_settings_name`).
These are the two whose `cache_info().currsize` the F2P test inspects.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `Apps` instance | minimal `Registry` class with only the two touched cache occupancies | only the observable state the reset touches/promises is modeled; unrelated `Apps` fields are irrelevant to the contracted behaviour |
| `method.cache_info().currsize` (a `functools._lru_cache_wrapper` occupancy: a non-negative int counting distinct argument tuples currently retained) | non-negative `int` field (`*_cache_occupancy`) | `currsize` ↔ the int field; `method.cache_clear()` sets `currsize` to `0` ↔ assigning `0` to the field |
| `self.get_models.cache_clear()` (`registry.py:378`) | `registry.models_cache_occupancy = 0` | `cache_clear()` empties that wrapper's cache ⇒ `currsize == 0`; modeled as assigning `0` |
| `self.get_swappable_settings_name.cache_clear()` (added by the patch at `registry.py:376`) | `registry.swappable_cache_occupancy = 0` | same: `cache_clear()` ⇒ `currsize == 0`; modeled as assigning `0` |
| the `if self.ready:` model-expiry loop (`registry.py:379-384`, `model._meta._expire_cache()`) | omitted | not part of the contracted behaviour: it expires per-model relation/field caches, which the F2P test does not observe (the test inspects only the two `cache_info().currsize` values). It performs NO `cache_clear()` on either of the two `@functools.cache` wrappers, so it cannot satisfy or affect the two zero-occupancy postconditions. Both pre- and post-patch keep it unchanged. |
| `clear_cache()` returns to its caller on every call (its body is two `cache_clear()` calls plus a bounded iteration over the finite `app_configs` dict — no unbounded loop or recursion) | `Requires(MustTerminate(2))` on `clear_all_caches`; `Requires(MustTerminate(1))` on `Registry.__init__` (strictly smaller measure, so construction inside a caller holding the obligation is admissible) | total-correctness obligation: the F2P observes the emptied caches only because the call RETURNS. A body that diverges (e.g. `while True: pass` before the clears) or re-enters the operation at a non-decreasing measure satisfies the zero-occupancy postconditions only vacuously and is rejected by Nagini's obligation-leak check. |

## 3. Callee provenance

No library callee is axiomatized. The single changed operation — clearing the
swappable-settings-name method's cache — is modeled **directly** as a state
write to that method's observable occupancy (`= 0`), exactly mirroring the
documented effect of `functools._lru_cache_wrapper.cache_clear()` on
`cache_info().currsize`.

### `functools.cache` / `cache_clear` / `cache_info().currsize` semantics (the only external fact relied on)
`functools.cache(f)` returns a `functools._lru_cache_wrapper` (it is
`lru_cache(maxsize=None)`). The wrapper exposes:
- `cache_info()` → a named tuple whose `currsize` is the number of distinct
  argument tuples currently memoized (the cache occupancy), always `>= 0`;
- `cache_clear()` → discards all memoized results, after which
  `cache_info().currsize == 0`.

Docs: https://docs.python.org/3/library/functools.html#functools.lru_cache
("`cache_clear()` … clear the cache") and
https://docs.python.org/3/library/functools.html#functools.cache. This is the
behaviour `axiom_check.py` (G-AX) exercises against the REAL `functools.cache`:
fill each wrapper, call `cache_clear()`, assert `currsize == 0` from any
starting occupancy. No `quote=`-style flag dependency applies.

## 4. Conformance check (G-CONF)

`conformance_check.py` runs the contract-stripped impl region (shadow)
against the real patched `Apps.clear_cache` (oracle) over >= 1e5
Requires-satisfying starting-occupancy pairs, lowered/raised through the §2
bridge (`cache_info().currsize` of each wrapper ↔ the two int fields).
Pinned fuzz seed: **17029** (the instance number).
