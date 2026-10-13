# refinement.md — django__django-11333

Operation correspondence between `Solution.lean`'s `do` block (`sharedHandle`)
and `patch.diff`. Every row is tagged **R** (type-only refinement), **I**
(identical concrete op), **A-consumed**, or **A-reference**. There are no
A-tagged ops in this bundle (no consumed axioms, no deep-model references).

## What the patch does

The gold patch makes the memoized lookup compute its cache key BEFORE the
memoized call instead of inside it:

```
# before (buggy): the lru_cache key is the RAW argument `urlconf`
@functools.lru_cache(maxsize=None)
def get_resolver(urlconf=None):
    if urlconf is None:
        urlconf = settings.ROOT_URLCONF        # normalization AFTER the key
    return URLResolver(RegexPattern(r'^/'), urlconf)

# after (fixed): normalize first, THEN take the memoized (cached) key
def get_resolver(urlconf=None):
    if urlconf is None:
        urlconf = settings.ROOT_URLCONF        # normalization BEFORE the key
    return _get_cached_resolver(urlconf)

@functools.lru_cache(maxsize=None)
def _get_cached_resolver(urlconf=None):
    return URLResolver(RegexPattern(r'^/'), urlconf)
```

Consequence: `get_resolver()` (arg `None`) and `get_resolver(ROOT_URLCONF)` now
hit the SAME cache key (`ROOT_URLCONF`), so they return the SAME, single
`URLResolver` object — one `_populate`, one cache. Before, `None` and
`ROOT_URLCONF` were distinct keys, building two distinct resolvers. The F2P test
asserts exactly this object identity:

```
self.assertIs(get_resolver(), get_resolver('urlpatterns.path_urls'))
self.assertIsNot(get_resolver(), get_resolver('urlpatterns.path_dynamic_urls'))
```

The companion edit in `django/urls/base.py` (`clear_url_caches` clears
`_get_cached_resolver.cache_clear()` instead of `get_resolver.cache_clear()`) is
the mechanical follow-through of renaming the lru_cached layer — it keeps the
cache-clearing helper pointed at the layer that now holds the cache. It is not
an independently-observable behavior (no F2P/P2P test distinguishes it; see
meta.json `additional_change_sites`), so it is shipped verbatim in `patch.diff`
for G-RESOLVE but not separately modeled.

## The single modeled behavior

The fix is entirely about WHICH key the shared object is stored under. We model
the returned object by its memoization key (`mapping.md` §2: object identity
⟺ key equality), as an `Option String`, and the fix as "resolve an omitted
identifier to the ambient default BEFORE taking the key."

| # | `do`-block op (`sharedHandle`) | `patch.diff` counterpart | tag | bijection / note |
|---|---|---|---|---|
| 1 | `let key := match requested with \| none => ambient \| some u => u` | `if urlconf is None: urlconf = settings.ROOT_URLCONF` — the normalization the patch moves to BEFORE the memoized call | **R** | `Option String` ↔ `urlconf` argument: Lean `none` ↔ Python `None`, `some s` ↔ the `str s`; `ambient` ↔ `settings.ROOT_URLCONF`. The resolved `key` ↔ the dotted name `_get_cached_resolver` is memoized on. |
| 2 | `return some key` | `return _get_cached_resolver(urlconf)` — fetch (memoized) the shared object stored under that key | **R** | Object identity ↔ key equality: the returned `some key` carries the storage key; two calls share one object iff their `key`s are equal. `some` (never `none`) ↔ a real `URLResolver` is always returned. Validated by G-CONF (`conformance_check.py`): for fuzzed request pairs, `shadow_key(a)==shadow_key(b)` iff `id(get_resolver(a))==id(get_resolver(b))`, both directions. |

No kind-3 row (no changed op inexpressible in Velvet). No A rows.

## Prepatch discriminator

`Solution_prepatch.lean` returns `requested` directly — i.e. the object's
identity is taken from the request AS RECEIVED, with the omitted→default
resolution happening (conceptually) only after identity is fixed. On
`requested = none` it returns `none`, but the spec requires
`some (lookupKey none ambient) = some ambient`. `prove_correct` fails on
exactly the clause `requested = some (lookupKey requested ambient)` with
`requested = none` (`none ≠ some ambient`) — the precise bug the F2P test
catches (`get_resolver()` ≠ `get_resolver(ROOT_URLCONF)`).
