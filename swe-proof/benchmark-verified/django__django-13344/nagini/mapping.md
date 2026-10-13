# mapping.md — django__django-13344

Binds every `model.py` symbol to its repository counterpart at
`base_commit = e39e727ded673e74016b5d3658d23cbe20234d11`, states the type
abstraction, and gives the provenance of the one axiom (callee source + the
exact behaviour the axiom encodes).

Repo files under change (all are the `__init__` of a `MiddlewareMixin`
subclass; every hunk replaces the hand-rolled body with `super().__init__(...)`):
`django/middleware/security.py`, `django/contrib/sessions/middleware.py`,
`django/middleware/cache.py` (three classes), and the shared base
`django/utils/deprecation.py` (`MiddlewareMixin.__init__`, the call target).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `Handler` (class, fields `producer`, `async_advertised`, `absence_signalled`) | a `MiddlewareMixin` instance and its three base-init-touched facets — `self.get_response`, the `_is_coroutine` marker (`asyncio.iscoroutinefunction(self)` truth), and the deprecation signal | minimal object carrying only the touched facets |
| `configure_handler(handler, producer)` | the patched `__init__(get_response)` of a plain subclass — `SecurityMiddleware.__init__` (`django/middleware/security.py:11`), `SessionMiddleware.__init__` (`django/contrib/sessions/middleware.py:15`), `UpdateCacheMiddleware.__init__` (`django/middleware/cache.py:66`), `FetchFromCacheMiddleware.__init__` (`django/middleware/cache.py:130`) — modelled by the shared base configuration | the modeled changed function (plain-subclass `__init__` ⇒ `super().__init__(get_response)`) |
| `configure_settings_handler(handler, producer, setting)` | the patched `CacheMiddleware.__init__(get_response, cache_timeout, page_timeout, **kwargs)` (`django/middleware/cache.py:175`), which calls `super().__init__(get_response)` and then configures its own settings | the modeled changed function (settings-carrying subclass `__init__`) |
| `producer_is_async(producer)` *(axiom — A-consumed)* | `asyncio.iscoroutinefunction` — CPython stdlib `Lib/asyncio/coroutines.py` (called in `MiddlewareMixin._async_check`, `django/utils/deprecation.py:105`) | unchanged stdlib callee deciding whether the producer is a coroutine function |
| `resolve_store(store_name)` *(axiom — A-consumed)* | `caches[alias]` — the cache registry read (`django.core.cache.caches`, `django/core/cache/__init__.py`); invoked in `UpdateCacheMiddleware.__init__`/`FetchFromCacheMiddleware.__init__` (`django/middleware/cache.py`) and the explicit-`cache_alias` branch of `CacheMiddleware.__init__` (`django/middleware/cache.py:175+`) | unchanged registry lookup mapping a cache-alias name to its cache backend |
| `Handler.store_name` / `Handler.store` (fields) | `CacheMiddleware`/parent's `self.cache_alias` (the selected cache alias) and `self.cache` (the resolved backend `caches[self.cache_alias]`) | the two field-coupled facets the constructor tests pin |

The base configuration the patch routes every subclass through is
`MiddlewareMixin.__init__` (`django/utils/deprecation.py:94-98`):

```python
def __init__(self, get_response=None):
    self._get_response_none_deprecation(get_response)   # fact (1)
    self.get_response = get_response                    # fact (2)
    self._async_check()                                 # fact (3)
    super().__init__()
```

with `_async_check` (`django/utils/deprecation.py:100-108`) setting the
`_is_coroutine` marker when `asyncio.iscoroutinefunction(self.get_response)` is
True, and `_get_response_none_deprecation` (`:141-147`) warning when
`get_response is None`.

The pre-patch repo symbols the change removes (for the refinement audit, not
referenced from the consumer spec view): each subclass `__init__` open-coded
`self._get_response_none_deprecation(get_response)` and
`self.get_response = get_response` but **omitted** the `self._async_check()`
call, so the `_is_coroutine` marker was never established (e.g.
`django/middleware/security.py:12-22`, no `_async_check`;
`django/middleware/cache.py:67-73`, etc.).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `get_response` (a callable response-producer, or `None`) | `Optional[int]` opaque token | the producer is identity-tracked; `None` ↔ the absent value (`get_response is None`); any non-`None` token ↔ a supplied producer |
| `self.get_response` attribute | `handler.producer` | direct field bijection (`is` identity preserved) |
| the `_is_coroutine` marker presence, observed as `asyncio.iscoroutinefunction(instance)` | `handler.async_advertised: bool` | True ⟺ instance reports as a coroutine function ⟺ marker set |
| the deprecation signal having fired for the absent producer | `handler.absence_signalled: bool` | True ⟺ `RemovedInDjango40Warning` was raised at construction |
| `CacheMiddleware`/parent `self.cache_alias` (the selected alias name) | `handler.store_name: int` | opaque alias-name token; the value `super().__init__` establishes by default vs. the explicit `cache_alias` kwarg override |
| `CacheMiddleware`/parent `self.cache` (`= caches[self.cache_alias]`, the resolved backend) | `handler.store: int` and `Result()` | the resolved store; the load-bearing invariant `store == resolve_store(store_name)` mirrors `self.cache == caches[self.cache_alias]` on every path |
| `default_name` / `override_name` parameters | the default alias from `settings.CACHE_MIDDLEWARE_ALIAS` (set via `super().__init__`) vs. an explicit `cache_alias=...` kwarg (`None` ↔ no override supplied) | drives the default vs. explicit-override construction path |
| `caches[alias]` (the registry read) | `resolve_store(store_name)` | the unchanged deterministic alias→backend lookup (kind-A, §3.3) |
| `asyncio.iscoroutinefunction(get_response)` | `producer_is_async(producer)` | the runtime predicate over the producer token (kind-A, §3) |

The incidental scalar settings the gold cache hunk also touches
(`cache_timeout`, `page_timeout`, `key_prefix`) carry no cross-field invariant
the bug changes and are not modeled (out of model scope; enforced by G-RESOLVE).
The one field-coupled invariant a wrong refinement could break,
`cache == caches[cache_alias]`, is modeled deeply via `store`/`store_name`.

There is no string content under this change; the carrier is opaque tokens and
booleans, so no `List[int]`/`PSeq` string modeling is needed.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `producer_is_async` ↔ `asyncio.iscoroutinefunction` (A-consumed)
**Callee:** CPython `asyncio.iscoroutinefunction(func)` — returns True if `func`
is a coroutine function (an `async def`), False otherwise; `None` and
non-callables return False. Source: `Lib/asyncio/coroutines.py`. Docs:
https://docs.python.org/3/library/asyncio-task.html#asyncio.iscoroutinefunction

The axiom encodes only the obligation the configuration proof relies on as a
hard fact — that the **absent** producer is not asynchronous:

  `producer is None  ⟹  producer_is_async(producer) is False`.

This is the weakest sufficient contract: the configuration spec leaves the
async/sync outcome on a *supplied* producer fully general (it is just
`producer_is_async(producer)`, an uninterpreted-but-deterministic value), and
only pins the `None` case, which the absence-signal fact also keys on. An
over-claim (e.g. asserting a particular non-`None` token is/ isn't async) is
avoided.

**Why this is the unchanged callee, not the changed op.** The changed operation
is the subclass `__init__`'s *control flow*: the patch makes it delegate to the
base init so that `_async_check()` (which calls `iscoroutinefunction`) actually
runs. `iscoroutinefunction` itself is unchanged — it is the callee the restored
`_async_check()` invokes. It is therefore axiomatized (A-consumed), while the
restored configuration behaviour is modeled deeply (the `configure_handler`
impl spelling out all three facts), validated as an **A-reference** in §3.2.

### 3.2 Configuration deep model ↔ `MiddlewareMixin.__init__` mechanism (A-reference)
The three facts `configure_handler` / `configure_settings_handler` establish
(producer retained; absence signal iff `None`; async advertised iff async
producer) are the spelled-out effects of the real `super().__init__(get_response)`
chain (`MiddlewareMixin.__init__` → `_get_response_none_deprecation` +
attribute store + `_async_check`). There is **no consumed axiom** for this; it
is modeled deeply and validated **== the real mechanism** out-of-band by
`axiom_check.py` (G-AX), which reproduces the exact stdlib machinery the patch
relies on — the `_is_coroutine = asyncio.coroutines._is_coroutine` marker set
inside `_async_check` exactly when `asyncio.iscoroutinefunction(get_response)`
is True, which is what makes `asyncio.iscoroutinefunction(instance)` report
True. No flag dependency applies (the predicate has no relevant kwargs).

**Soundness check (G-AX):** `axiom_check.py` runs the real
`asyncio.iscoroutinefunction` on the absent value plus sync/async/non-callable
producer tokens (boundary) and 4000 randomized fuzz tokens, asserting the
A-consumed axiom (`None → False`, determinism, exact match). It also reproduces
the `super().__init__` marker mechanism (stdlib `asyncio` + `warnings` only, no
django import) and asserts the resulting (stored producer, absence-signalled,
async-advertised-via-`iscoroutinefunction(instance)`) triple equals the model's
three facts on every token. Exit 0 iff sound.

### 3.3 `resolve_store` ↔ `caches[alias]` registry read (A-consumed) + store-selection (A-reference)
**Callee:** `caches[alias]` — the Django cache registry read
(`django.core.cache.caches`, `django/core/cache/__init__.py`), a connection
handler that maps a cache-alias name to its configured backend. It is an
**unchanged** keyed mapping read invoked by the (unchanged-in-this-respect)
`UpdateCacheMiddleware`/`FetchFromCacheMiddleware` base inits and by the explicit-
`cache_alias` branch of `CacheMiddleware.__init__`. The bug does not change this
callee — it changes the *control flow* of `CacheMiddleware.__init__` (delegating
defaults to `super().__init__`, then conditionally overriding alias + re-deriving
the store inside the same branch).

The axiom encodes only the property the proof relies on as a hard fact —
**determinism**: `resolve_store(name)` is a deterministic function of the name
(same name → same store). It does NOT claim distinct names map to distinct
stores, nor any particular store value; the supplied-name → store outcome is left
uninterpreted-but-deterministic. This is the weakest sufficient contract: the
load-bearing invariant `store == resolve_store(store_name)` is provable from the
impl assigning `store = resolve_store(store_name)` with the final `store_name`,
and consumers of the spec get exactly the `cache == caches[cache_alias]`
guarantee the constructor tests assert, no more.

**Why this is the unchanged callee, not the changed op.** The changed operation
is `CacheMiddleware.__init__`'s control flow (where defaults come from and that
an explicit alias override re-derives the store). `caches[...]` itself is the
unchanged registry the override branch invokes — so it is axiomatized
(A-consumed), while the override-and-re-derive control flow is modeled deeply
(`configure_settings_handler` B2–B4), validated as an A-reference below.

**Soundness check (G-AX):** `axiom_check.py` reproduces the `caches[alias]`
registry read with a stdlib `dict` (the relied-on machinery is a keyed lookup)
and asserts determinism on all boundary alias names + fuzz. It also reproduces
the patched `CacheMiddleware.__init__` store-selection control flow (defaults
from `super().__init__`, then a conditional override that re-selects the name AND
re-resolves `store = caches[name]`) and asserts the load-bearing invariant
`store == resolve_store(store_name)` and `store_name == (override if supplied
else default)` on every default/explicit-default/explicit-custom name pair
(boundary, including known + unknown aliases and the None-override default path,
plus randomized fuzz). No django import; no flag dependency (a plain mapping
read). Exit 0 iff sound.
