# mapping.md — django__django-11333

Binds every model symbol to its repo counterpart at `base_commit`
`55b68de643b5c2d5f0a8ea7587ab3b2966021ccc`, states the type abstraction, and
records callee provenance. No callee is axiomatized (the whole behaviour is
modelled deeply), so there is no axiom-provenance section.

## 1. Symbol binding

| model symbol (`model.py`) | repo symbol | repo location (base_commit) | role |
|---|---|---|---|
| `get_resolver(cache, selector, cached, existing, fresh)` | `django.urls.resolvers.get_resolver(urlconf)` | `django/urls/resolvers.py:66-70` | the modeled changed function: the memoized routing-table lookup |
| `cached` (`bool`), `existing` (`int`) | the entry state of the `lru_cache` memo for the resolved key (whether it already holds an object, and which) | `django/urls/resolvers.py:66/73` (the memo) | pre-state scalars capturing "the resolved selector was already cached, holding `existing`", so the memoization guarantee gates on a genuine entry fact (the django-12713 pattern) rather than on a query against the mutated cache |
| `resolve_selector(selector)` | the expression `urlconf if urlconf is None else …` normalization, i.e. `if urlconf is None: urlconf = settings.ROOT_URLCONF` | `django/urls/resolvers.py:68-69` (post-patch hoisted into `get_resolver`; pre-patch lived INSIDE the cached body) | the omitted-means-default substitution |
| `default_selector()` | `settings.ROOT_URLCONF` | `django/conf` (the process-wide root URLconf) | the default selector substituted when the argument is omitted |
| `cache` (`Dict[int,int]`) | the `functools.lru_cache(maxsize=None)` memo table backing the cached resolver constructor | `django/urls/resolvers.py:66` (pre-patch decorator on `get_resolver`); `:73` (post-patch decorator on `_get_cached_resolver`) | the shared memoization cache |
| `fresh` (`int`) | the identity of a newly constructed `URLResolver(RegexPattern(r'^/'), urlconf)` | `django/urls/resolvers.py:70` (post-patch `_get_cached_resolver` body, `:75`) | a not-yet-cached routing-table object's identity |
| `Result()` (`int`) | the `URLResolver` object returned by `get_resolver` | `django/urls/resolvers.py:70` | the handed-back routing table's identity |

The companion edit `django/urls/base.py` (the import of `_get_cached_resolver`
and `clear_url_caches` calling `_get_cached_resolver.cache_clear()` instead of
`get_resolver.cache_clear()`, `django/urls/base.py:10,95`) is a mechanical
follow-on of moving the `@lru_cache` from `get_resolver` to the new
`_get_cached_resolver`: the cache to clear is the one that now holds the
entries. It is the same cache object the model's `cache` parameter abstracts;
it has no separately-observable behaviour beyond "the cache `get_resolver`
populates is the cache `clear_url_caches` clears", which the single modeled
cache already captures. No separate modeled function is needed.

## 2. Type abstraction

| repo reality | model carrier | justification |
|---|---|---|
| `urlconf`: `Optional[str]` (a dotted module path, or `None` meaning "use the default") | `selector: Optional[int]` | only equality/identity of urlconf VALUES is observed (which cache slot a urlconf maps to, and whether two urlconfs are the equal key); a `str` is an opaque equality token, faithfully carried by an `int`. `None` ↔ `None` exactly. Nagini bans `str` indexing; no indexing is needed here. |
| `settings.ROOT_URLCONF`: a fixed `str` | `default_selector() == 0` | the default is one fixed selector value; its concrete identity is irrelevant, only that it is the value `None` resolves to and that an explicit argument equal to it shares the slot (which the tests exercise: `ROOT_URLCONF='urlpatterns.path_urls'`). |
| `functools.lru_cache(maxsize=None)` memo (key = call arguments) | `cache: Dict[int,int]` keyed by resolved selector → object-identity token | `lru_cache(maxsize=None)` is an unbounded memo: a key already seen returns the stored result; a new key constructs and stores. A `Dict` from key to a result-identity token is the faithful abstraction; `maxsize=None` ⇒ no eviction ⇒ the cache only grows (modeled by the no-key-dropped postcondition). |
| `URLResolver(...)` object IDENTITY (`is`/`is not` in the F2P test) | distinct `int` tokens; equal tokens = same object, distinct tokens = distinct objects | the F2P test compares with `assertIs`/`assertIsNot`, i.e. object identity, never object contents. Integer identity is the faithful carrier of "same/different object". |
| constructing a NEW `URLResolver` for an uncached key | the `fresh: int` parameter, precondition-constrained `!= existing` (the already-cached object) when the slot pre-exists | a freshly constructed object has a brand-new identity, distinct from the object already cached for that key; modeled by `Implies(cached, existing != fresh)`. |
| the ENTRY state of the memo for the resolved key (already-cached? which object?) | pre-state scalars `cached: bool`, `existing: int` (preconditions `cached == (resolve_selector(selector) in cache)`, `Implies(cached, cache[resolve_selector(selector)] == existing)`) | the memoization guarantee must gate on the genuine ENTRY state, not on a query against the in-place-mutated cache (which an impl could perturb by writing the slot itself, and which exposes a Nagini `Old`-of-written-Dict-key unsoundness — refinement.md §E). Lifting the entry membership/value into scalars (the django-12713 pattern) is sound and makes the over-construct adversary fail. `maxsize=None` ⇒ the memo is single-valued and never-evicted, so each real call supplies one consistent valuation. |

## 3. Callee provenance

None. There is no axiomatized callee. The construction of a routing table for an
uncached key (`URLResolver(RegexPattern(r'^/'), urlconf)`) is abstracted purely
as "allocate a fresh identity token", because the tested behaviour
(`assertIs`/`assertIsNot`) observes only WHICH cache slot a request maps to and
whether two requests share an object — never the constructed object's contents.
The `@lru_cache` semantics are modeled deeply (the lookup-or-insert in the impl
region), not axiomatized. `functools.lru_cache(maxsize=None)` provenance:
CPython `Lib/functools.py` (`_lru_cache_wrapper`, `maxsize=None` branch: a plain
dict memo keyed by the call arguments, no eviction);
docs.python.org/3/library/functools.html#functools.lru_cache.

## 4. The F2P test, under the abstraction

`tests/urlpatterns/test_resolvers.py::ResolverCacheTests`, with
`@override_settings(ROOT_URLCONF='urlpatterns.path_urls')`:

* `self.assertIs(get_resolver(), get_resolver('urlpatterns.path_urls'))`
  — `get_resolver()` omits the selector (`selector=None`), `get_resolver('…path_urls')`
  supplies the default explicitly. Both resolve to `default_selector()`, so both
  map to the SAME cache slot ⇒ the same object. Modeled by
  `Result() == cache[resolve_selector(selector)]` with
  `resolve_selector(None) == resolve_selector(default) == default_selector()`.
  Pre-patch keys on the raw argument, so the omitted call lands in a separate
  "no-argument" slot and builds a second object ⇒ the assertion fails.

* `self.assertIsNot(get_resolver(), get_resolver('urlpatterns.path_dynamic_urls'))`
  — the second selector resolves to a value `!= default_selector()`, so it owns a
  distinct cache slot ⇒ a distinct object. Modeled by the per-other-key
  distinctness postcondition (`k != resolve_selector(selector) ⇒ cache[k]` is its
  own untouched object).
