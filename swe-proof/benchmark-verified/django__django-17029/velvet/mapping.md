# mapping.md — django__django-17029

Binds `Solution.lean` symbols to the repo at
`base_commit = 953f29f700a60fc09b08b2c2270c12c447490c6a`, states the type
abstraction, and records callee provenance.

Repo file under change: `django/apps/registry.py` (`Apps.clear_cache`).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `clearAllCaches (mut modelsOccupancy) (mut swappableOccupancy)` | `Apps.clear_cache(self)` — `django/apps/registry.py:370` (body 376-384) | the modeled changed function (the registry's cache-reset operation) |
| `modelsOccupancy` (`mut`) | `Apps.get_models`'s `functools.cache` cache occupancy, i.e. `Apps.get_models.cache_info().currsize` (`get_models` defined `registry.py:168-169`, `@functools.cache`) | observable occupancy of the all-models lookup cache |
| `swappableOccupancy` (`mut`) | `Apps.get_swappable_settings_name`'s `functools.cache` cache occupancy, i.e. `Apps.get_swappable_settings_name.cache_info().currsize` (`get_swappable_settings_name` defined `registry.py:283-284`, `@functools.cache`) | observable occupancy of the swappable-settings-name lookup cache |
| `unit` (return) | `clear_cache` returns `None` | no value returned |

The two memoizing methods are exactly the two methods on `Apps` decorated with
`@functools.cache` (`functools.cache == functools.lru_cache(maxsize=None)`),
confirmed by `grep '@functools.cache' django/apps/registry.py` at base_commit:
lines 168 (`get_models`) and 283 (`get_swappable_settings_name`). These are the
two whose `cache_info().currsize` the F2P test (`test_clear_cache`) inspects.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

| repo reality | Lean carrier | bijection |
|---|---|---|
| `Apps` instance | only the two touched cache occupancies, modeled as two `mut Nat` method parameters | only the observable state the reset touches/promises is modeled; unrelated `Apps` fields are irrelevant to the contracted behaviour |
| `method.cache_info().currsize` (a `functools._lru_cache_wrapper` occupancy: a non-negative int counting distinct argument tuples currently retained) | `Nat` (`*Occupancy`) | `currsize` ↔ the `Nat`; non-negative, exact. `method.cache_clear()` sets `currsize` to `0` ↔ assigning `0` to the field |
| `self.get_models.cache_clear()` (`registry.py:378`) | `modelsOccupancy := 0` | `cache_clear()` empties that wrapper's cache ⇒ `currsize == 0`; modeled as assigning `0` |
| `self.get_swappable_settings_name.cache_clear()` (added by the patch, becomes `registry.py:376`) | `swappableOccupancy := 0` | same: `cache_clear()` ⇒ `currsize == 0`; modeled as assigning `0` |
| the `if self.ready:` model-expiry loop (`registry.py:379-384`, `model._meta._expire_cache()`) | omitted | not part of the contracted behaviour: it expires per-model relation/field caches, which the F2P test does not observe (the test inspects only the two `cache_info().currsize` values). It performs NO `cache_clear()` on either of the two `@functools.cache` wrappers, so it cannot satisfy or affect the two zero-occupancy postconditions. Both pre- and post-patch keep it unchanged. |

## 3. Callee provenance

No library callee is **axiomatized** (no consumed contract). The single changed
operation — clearing the swappable-settings-name method's cache — is modeled
**directly** as a state write to that method's observable occupancy
(`swappableOccupancy := 0`), exactly mirroring the documented effect of
`functools._lru_cache_wrapper.cache_clear()` on `cache_info().currsize`.

### `functools.cache` / `cache_clear` / `cache_info().currsize` semantics (the only external fact relied on)
`functools.cache(f)` returns a `functools._lru_cache_wrapper` (it is
`lru_cache(maxsize=None)`). The wrapper exposes:
- `cache_info()` → a named tuple whose `currsize` is the number of distinct
  argument tuples currently memoized (the cache occupancy), always `>= 0`;
- `cache_clear()` → discards all memoized results, after which
  `cache_info().currsize == 0`.

Docs: https://docs.python.org/3/library/functools.html#functools.lru_cache
("`cache_clear()` … clear the cache") and
https://docs.python.org/3/library/functools.html#functools.cache. This is an
**A-reference** (refinement.md A2/A3): the fact `cache_clear() ⇒ currsize == 0`
is about the UNCHANGED stdlib `functools.cache` callee, validated == the real
callee out-of-band by `axiom_check.py` (G-AX): fill each wrapper, call
`cache_clear()`, assert `currsize == 0` from any starting occupancy. No
`quote=`-style flag dependency applies.

## 4. G-CONF — conf_skip=true (documented reason)

`conformance_check.py` is a `status=skip` stub. The impl region's executable
content is the pure state mutation `modelsOccupancy := 0; swappableOccupancy := 0`
— clearing the live `functools._lru_cache_wrapper` caches of two `Apps` methods.
There is no DB-free / state-free input-dependent R/I shadow to differential-test:

- The only observable the fix produces is a **side effect on a live registry
  object** (each wrapper's `cache_info().currsize` becomes `0`). Reproducing it
  requires standing up the global `Apps` registry with installed apps, priming
  both caches, then calling `clear_cache()` and reading `cache_info()` — i.e. the
  F2P integration test itself (`test_clear_cache`), not a pure transliteration
  this gate can fuzz over ≥1e5 inputs.
- The changed op's content (`swappableOccupancy := 0`) is a constant state
  mutation; its only R/I shadow would be the constant `0`. Diffing `0 == 0`
  carries no information — there is no input-dependent computation to refute.

Per SPEC_GUIDE §0 / WORKER_PROMPT: when the impl region is the deep state
mutation of a live registry object with no state-free R/I shadow, set
`meta.json conf_skip=true` and ship a `status=skip` stub. Soundness of the
modeled mutation is carried instead by **G-VERIFY** (the spec provably forces
both occupancies to `0` on return), **G-DIFF** (the prepatch, which never assigns
`swappableOccupancy`, fails exactly the `swappableOccupancy = 0` clause — see
refinement.md §B), and the single `functools.cache` A-reference fact (G-AX,
`axiom_check.py`).

## 5. Notes

The model is the genuine-`mut` form (directive 5 showcase): both occupancy
counters are declared `mut`, each assigned `:= 0`, and each post-state pinned to
the exact value `0`. There is no read-only `mut` (directive 5): both parameters
are genuinely written.
