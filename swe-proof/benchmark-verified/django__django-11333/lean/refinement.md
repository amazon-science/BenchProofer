# refinement.md — django__django-11333

Maps every operation in `implementation_cachedLookup` to its `patch.diff`
counterpart in `django/urls/resolvers.py::get_resolver` (the modeled
representative — see mapping.md). Tags: **R** type-refinement, **A-consumed**
proof uses a callee axiom, **A-reference** deep-modeled changed op validated ==
real callee, **I** identical concrete op.

## Patch (post-patch `get_resolver` + extracted memoized factory)
```python
def get_resolver(urlconf=None):
    if urlconf is None:
        urlconf = settings.ROOT_URLCONF
    return _get_cached_resolver(urlconf)


@functools.lru_cache(maxsize=None)
def _get_cached_resolver(urlconf=None):
    return URLResolver(RegexPattern(r'^/'), urlconf)
```

## Operation correspondence
| # | Lean op (`implementation_cachedLookup`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `let mut key := config` | `def get_resolver(urlconf=None):` — the raw argument enters | R | `str | None ↔ Option String`; `None ↔ none`, `s ↔ some s`. |
| 2 | `if key = none then key := some defaultConfig` | `if urlconf is None: urlconf = settings.ROOT_URLCONF` | R | the normalization the fix relies on: an omitted configuration is resolved to the default configuration *before* the memoized lookup. `defaultConfig ↔ settings.ROOT_URLCONF`. This is the behavioral edit: pre-patch this normalization happened INSIDE the memoized body (after the cache key was taken), so the omitted call and the explicit-default call landed in different cache slots. |
| 3 | `return buildArtifact key` | `return _get_cached_resolver(urlconf)` | R | present the (now-normalized) key to the unchanged memoized factory. `buildArtifact : Option String → Artifact ↔` the `lru_cache`-wrapped `URLResolver(RegexPattern(r'^/'), key)`. Equal keys ⇒ identical cached object (CPython `is`), modeled by `buildArtifact` being an ordinary function (equal args ⇒ equal result). |

Every op is R; **no A row** is *consumed*: `buildArtifact` is declared `opaque`
purely so the unchanged memoized factory can appear in the executable impl, and
the proof closes by case analysis on `config` + reflexivity (`problem_spec` pins
the result to `buildArtifact (some (config.getD defaultConfig))`, which the impl
computes verbatim). No `axiom buildArtifact_prop` is declared, so there is no
A-consumed and no A-reference. Therefore `meta.json axioms = []`,
`deep_model_references = []`, and `axiom_check.py` is a skip stub.

## R legs ⇒ G-CONF
The impl is all R (no A-tagged op), so `conformance_check.py` mechanically
differential-tests the impl shadow against `patch.diff` behavior. The modeled
observable is OBJECT IDENTITY, which for a memoized factory equals equality of
the (post-normalization) cache key: the shadow computes `norm_key(config,
defaultConfig)` and predicts two lookups are identical iff their normalized keys
are equal; the real leg drives the patched `get_resolver` and tests CPython
`is`. Asserted equal over ≥10^5 fuzzed `(defaultConfig, a, b)` triples.
`conf_skip = false`.

## Prepatch = the real bug
`Solution_prepatch.lean` omits op #2: it presents the RAW key to the factory
(`return buildArtifact key` with `key := config`, no normalization). That is
exactly the pre-patch `get_resolver`, where `@lru_cache` wrapped the whole
function so the raw argument was the cache key and the `None`→default
normalization happened only afterward, inside the cached body. On an omitted
lookup (`config = none`) the prepatch yields `buildArtifact none`, which is not
provably equal to `buildArtifact (some defaultConfig)` (distinct opaque
applications — distinct cache slots, distinct objects). It therefore cannot
satisfy `problem_spec_cachedLookup` (which demands `result = buildArtifact (some
(config.getD defaultConfig))`), so its `correct_cachedLookup` is unclosable ⇒
G-DIFF fails verification as required. This is precisely the FAIL_TO_PASS
behavior: `get_resolver()` (omitted) and `get_resolver(ROOT_URLCONF)` (explicit
default) must be the IDENTICAL object (`assertIs`); pre-patch they were two
distinct objects.

## Sibling site (NOT separately modeled — behavior-preserving cache-key rename)
`patch.diff` also edits `django/urls/base.py::clear_url_caches`
(`get_resolver.cache_clear()` → `_get_cached_resolver.cache_clear()`) and the
corresponding import. This is NOT an independent behavioral fix: post-patch the
`lru_cache` lives on `_get_cached_resolver` rather than on `get_resolver`, so
the cache-clearing call is renamed to target the same cache. It clears the same
memoized state and changes no observable lookup behavior. Only `get_resolver`'s
key-normalization-before-memoization changes the modeled behavior, and only that
is exercised by the FAIL_TO_PASS test. `patch.diff` (gold verbatim) applies both
edits so the official harness resolves.
