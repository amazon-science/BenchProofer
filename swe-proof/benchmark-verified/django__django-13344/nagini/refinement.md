# refinement.md — django__django-13344

The operation-by-operation correspondence between `model.py`'s implementation
(`configure_handler`, `configure_settings_handler`, the `producer_is_async` and
`resolve_store` axioms) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — split into **A-consumed**, where the
proof uses the axiom's `Ensures`, and **A-reference**, where a deep model is
validated == the real callee/mechanism by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## Background: what the patch does

The gold patch edits the `__init__` of five `MiddlewareMixin` subclasses
(`SecurityMiddleware`, `SessionMiddleware`, `UpdateCacheMiddleware`,
`FetchFromCacheMiddleware`, `CacheMiddleware`). Each one had open-coded part of
the base initializer — `self._get_response_none_deprecation(get_response)` and
`self.get_response = get_response` — but **omitted** the base init's third step,
`self._async_check()`. The patch replaces those open-coded lines with
`super().__init__(get_response)`, which runs all three base steps. The base
`MiddlewareMixin.__init__` (`django/utils/deprecation.py:94`) is:

```python
self._get_response_none_deprecation(get_response)   # (1) deprecation signal
self.get_response = get_response                     # (2) retain producer
self._async_check()                                  # (3) set _is_coroutine marker
```

`_async_check()` sets the `_is_coroutine` marker when
`asyncio.iscoroutinefunction(self.get_response)` is True; that marker is what
makes `asyncio.iscoroutinefunction(instance)` report True downstream.

## A. Plain-subclass sites — `configure_handler`

Representative gold hunk (`django/middleware/security.py`; the
`SessionMiddleware`, `UpdateCacheMiddleware`, `FetchFromCacheMiddleware` hunks
are the same shape):

```
-        self._get_response_none_deprecation(get_response)
+        super().__init__(get_response)
         self.sts_seconds = settings.SECURE_HSTS_SECONDS
         ...
-        self.get_response = get_response
```

| # | model.py impl op (`configure_handler`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `handler: Handler` with fields `producer`/`async_advertised`/`absence_signalled` | the middleware instance `self` and its base-init-touched facets | R | object ↔ minimal class on the touched fields (mapping.md §1, §2). |
| A2 | `producer: Optional[int]` | the `get_response` argument | R | callable-or-`None` ↔ opaque token; `None` ↔ the absent value (mapping.md §2). |
| A3 | `if producer is None: handler.absence_signalled = True else: ... = False` | `_get_response_none_deprecation(get_response)` invoked by `super().__init__` (warns iff `get_response is None`) | A-reference | the deprecation-signal step is modeled **deeply** (the guarded boolean fact `absence_signalled == (producer is None)`); validated == the real `super().__init__` warning behaviour by axiom_check.py (G-AX). No consumed axiom. |
| A4 | `handler.producer = producer` | `self.get_response = get_response` (done by `super().__init__`) | I | identical attribute store; field bijection (mapping.md §2). |
| A5 | `handler.async_advertised = producer_is_async(producer)` | `self._async_check()` invoked by `super().__init__` (sets the `_is_coroutine` marker iff `iscoroutinefunction(get_response)`) | A-consumed + A-reference | the *value* `producer_is_async(producer)` is the **A-consumed** axiom on the unchanged stdlib callee `asyncio.iscoroutinefunction` (mapping.md §3.1); the *fact that this step runs at all* (the restored marker mechanism) is the **A-reference** validated == the real `super().__init__` marker behaviour by G-AX (mapping.md §3.2). |

## B. Settings-carrying site — `configure_settings_handler`

Gold hunk (`django/middleware/cache.py`, `CacheMiddleware.__init__`):

```
-        self._get_response_none_deprecation(get_response)
-        self.get_response = get_response
+        super().__init__(get_response)
         ... key_prefix / cache_alias / cache_timeout configuration ...
```

The cache hunk is **not** a pure store-then-expose: the gold patch genuinely
*restructures* the alias/store computation. Pre-patch each branch unconditionally
recomputed `self.cache_alias` and then set `self.cache = caches[self.cache_alias]`
once at the end. Post-patch the defaults come from `super().__init__` (through the
`UpdateCacheMiddleware`/`FetchFromCacheMiddleware` base inits, which set
`cache_alias = settings.CACHE_MIDDLEWARE_ALIAS` and `cache = caches[cache_alias]`),
and an explicit `cache_alias` kwarg *both* re-selects the alias *and* re-derives
`self.cache = caches[self.cache_alias]` inside the same branch. Three
PASS_TO_PASS tests pin the resulting invariant — `test_constructor` (now also
asserting `middleware.cache == self.other_cache` / `== self.default_cache`),
`test_update_cache_middleware_constructor`, and
`test_fetch_cache_middleware_constructor` (both new) — all assert
`middleware.cache == caches[middleware.cache_alias]` on the default, explicit-
default, and explicit-custom paths. So this is a **changed operation that must be
modeled deeply**, not an "I" row.

| # | model.py impl op (`configure_settings_handler`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | steps A3–A5 (the three shared facts) | `super().__init__(get_response)` | A-reference + A-consumed + I | identical to site A; the same delegation establishes the same three facts (mapping.md §3). |
| B2 | `handler.store_name = default_name; handler.store = resolve_store(handler.store_name)` (defaults established as super().__init__ does) | the default alias + store set by the base init via `super().__init__` (`self.cache_alias = settings.CACHE_MIDDLEWARE_ALIAS; self.cache = caches[self.cache_alias]`) | R + A-consumed | object/field bijection: `store_name` ↔ `cache_alias`, `store` ↔ `cache` (mapping.md §2); the alias→store resolution `resolve_store` is the **A-consumed** axiom on the unchanged `caches[...]` registry read (mapping.md §3.3). |
| B3 | `if override_name is not None: handler.store_name = override_name; handler.store = resolve_store(handler.store_name)` | the explicit-`cache_alias`-kwarg branch (`self.cache_alias = cache_alias; self.cache = caches[self.cache_alias]`) | R + A-consumed | the deeply-modeled override control flow: an explicit name re-selects the alias AND re-derives the store from the new alias, exactly as the gold branch does. Pins the load-bearing invariant `store == resolve_store(store_name)` the 3 constructor tests assert. |
| B4 | `return handler.store` (with `Ensures(Result() == handler.store)`) | the constructed middleware whose `.cache`/`.cache_alias` the constructor tests then observe | I | the configured store reported back; identical expose of the just-computed field. |

The other subclass-specific settings the patch also touches (`cache_timeout`,
`page_timeout`, `key_prefix`) are *settings-driven scalar stores* with no cross-
field invariant beyond direct assignment, and the bug does not change how they
are stored; they are out of model scope and enforced only by the SWE-bench
oracle (G-RESOLVE). The single field-coupled invariant a wrong refinement could
break — `cache == caches[cache_alias]` — is the one this row models deeply, so
no model-satisfying refinement can drop the store re-derivation those 3 P2P
tests pin.

## C. The discriminating change and the prepatch

The discriminating content of the fix is step **A5/B1**: the restored
`_async_check()` (i.e. `handler.async_advertised = producer_is_async(producer)`).
Pre-patch, every subclass `__init__` did A3 and A4 but **skipped** A5, so the
marker was never set and `asyncio.iscoroutinefunction(instance)` was always
False — the first middleware in a chain then received an unresolved coroutine
instead of a materialised response. `model_prepatch.py` reproduces exactly this
omission (it sets `absence_signalled` and `producer`, and still establishes the
store-selection facts B2–B4 correctly, but never assigns `async_advertised`) and
**fails** the postcondition
`handler.async_advertised == producer_is_async(producer)` in BOTH
`configure_handler` and `configure_settings_handler` — precisely the spec
sensing the change (G-DIFF). This is the single independently-fixed *behavioural*
delta (the restored coroutine marker), shared verbatim across all five sites, so
one prepatch (covering both the plain and the settings-carrying shape) is the
complete differential witness for it. (The cache-settings restructure B2–B4 is a
non-discriminating refactor carried by the same gold hunk; it is modeled deeply
so that `verify(model)` *entails* the constructor P2P tests, but it is not a
separate failing prepatch because the pre-patch code also satisfied
`cache == caches[cache_alias]`.)

The deprecation fact A3 (`absence_signalled == (producer is None)`) is the
property the F2P `test_deprecation`/`test_passing_explicit_none` observe; it
already held pre-patch via the open-coded `_get_response_none_deprecation`
call, and continues to hold post-patch via `super().__init__`. The spec pins it
so that no impl can verify while dropping the deprecation signal.

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, A-reference, or I — **including the cache
hunk**, which is now modeled deeply (B2–B4, R + A-consumed on `resolve_store`)
rather than tagged "I". The operation that genuinely changed — the subclass
`__init__` *delegating to the base init so the coroutine-marker step runs* — is
modeled **deeply** (the three facts spelled out in `configure_handler`, with A5
consuming the `producer_is_async` axiom on the unchanged stdlib predicate), not
hidden behind an axiom about the function under change. The two consumed axioms,
`producer_is_async` and `resolve_store` (**A-consumed**), both cover **unchanged**
callees (`asyncio.iscoroutinefunction` invoked by the restored `_async_check()`;
the `caches[...]` registry read invoked by the store-selection branches); the
configuration *mechanism* and the *store-selection control flow* appear only as
the **A-reference** that G-AX validates the deep model against.

## E. verify(model) ⇒ resolved (scope-correct statement)

`configure_handler` / `configure_settings_handler` verify only if they establish:
producer retained (A4/I), absence-signal iff `None` (A3), the discriminator —
async-advertised iff the producer is async (A5, `== producer_is_async(producer)`)
— and, for the store-selecting variant, the load-bearing invariant
`store == resolve_store(store_name)` on the default / explicit-default /
explicit-custom paths (B2–B4). By R (object ↔ minimal class, token ↔
`get_response`, `store_name` ↔ `cache_alias`, `store` ↔ `cache`) the verified
configuration equals what `super().__init__(get_response)` plus the gold cache
hunk establish on every subclass; by G-AX the deep configuration model equals the
real `super().__init__` marker mechanism (A-reference), the real
`asyncio.iscoroutinefunction` meets the `producer_is_async` axiom (A-consumed,
`None → False`), and the real `caches[...]` registry read meets the
`resolve_store` axiom (A-consumed, deterministic) with the store re-derivation
discipline validated as an A-reference.

**Scope statement (corrected per the panel audit).** This entailment covers the
bug-delta (the restored coroutine marker) *and* every field-coupled invariant a
PASS_TO_PASS test the test_patch adds/modifies pins on a changed function — here,
the `cache == caches[cache_alias]` invariant the three constructor tests assert,
now modeled deeply (B2–B4). The remaining incidental scalar settings the gold
cache hunk also touches (`cache_timeout`, `page_timeout`, `key_prefix`) carry no
cross-field invariant the bug changes; they are explicitly **out of model scope**
and enforced solely by the SWE-bench oracle (G-RESOLVE), which the gold patch
passes. With this scoping, no implementation that verifies against the frozen
spec, refined by the map above, can diverge from the gold patch on any property
a F2P or constructor-P2P test pins — so it resolves. The trust points are exactly
the two of PLAN §1.1: axiom soundness (G-AX) and refinement fidelity (this
document, G-EQ).
