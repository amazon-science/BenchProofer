# mapping.md — django__django-11333

## Symbol binding (file:line @ base_commit 55b68de643b5c2d5f0a8ea7587ab3b2966021ccc)

Modeled function: `cachedLookup` (Lean) ↔ `get_resolver`
(`django/urls/resolvers.py:66-70` @ base_commit).

Pre-patch source (the bug):

```python
@functools.lru_cache(maxsize=None)
def get_resolver(urlconf=None):
    if urlconf is None:
        urlconf = settings.ROOT_URLCONF
    return URLResolver(RegexPattern(r'^/'), urlconf)
```

Post-patch source (the fix — split into a thin normalizer + a memoized factory):

```python
def get_resolver(urlconf=None):
    if urlconf is None:
        urlconf = settings.ROOT_URLCONF
    return _get_cached_resolver(urlconf)


@functools.lru_cache(maxsize=None)
def _get_cached_resolver(urlconf=None):
    return URLResolver(RegexPattern(r'^/'), urlconf)
```

The observable defect: the memoization (`functools.lru_cache`) is keyed on the
*raw* argument. Pre-patch, calling with no argument caches the constructed
object under the key `None`, while calling with the active default
configuration string caches under a *different* key — so the two calls build
and store **two distinct** objects even though both denote the identical
effective configuration (the issue's "multiple URLResolvers ... unintentionally
constructed", `URLResolver._populate` run twice). The fix resolves the argument
to its effective value *before* the memoized lookup, so both calls share one
cache slot and return the **identical** object. This is exactly what the
FAIL_TO_PASS test asserts:

```python
self.assertIs(get_resolver(), get_resolver('urlpatterns.path_urls'))      # SAME object
self.assertIsNot(get_resolver(), get_resolver('urlpatterns.path_dynamic_urls'))
```
(under `@override_settings(ROOT_URLCONF='urlpatterns.path_urls')`).

The newly added behavior is the `assertIs` (identity *collapse* of the
no-argument call and the explicit-default call). The `assertIsNot` (distinct
configs ⇒ distinct objects) already held pre-patch and is not the discriminator.

## Lean ↔ Python type bijection (used by G-CONF and G-AX)

| Lean | Python | note |
|---|---|---|
| `config : Option String` | the `urlconf` argument of `get_resolver` (`str | None`) | `none ↔ None` (argument omitted / passed `None`); `some s ↔ s` (an explicit configuration module path) |
| `defaultConfig : String` | `settings.ROOT_URLCONF` (`str`) | the active default configuration; always a module-path string |
| `result : Artifact` | the `URLResolver` object returned by `get_resolver(...)` | identity matters (`assertIs`/`assertIsNot`); internal fields are NOT modeled — `Artifact` is an abstract handle whose equality models Python object identity |
| `buildArtifact : Option String → Artifact` | the memoized factory keyed on its argument — the `lru_cache`-wrapped construction `URLResolver(RegexPattern(r'^/'), key)` | equal keys ⇒ the **identical** cached object; the cache key space is `Option String` so the pre-patch `None`-keyed slot is expressible. UNCHANGED by the patch. |

Bridge: a Lean `String` corresponds to the Python `str` of identical code
points; `Option String` carries the `str | None` argument. Object identity in
CPython (`is`) corresponds to `=` on `Artifact`: two `get_resolver` calls return
the same object iff their (post-normalization) `lru_cache` keys are equal, which
is precisely `buildArtifact k₁ = buildArtifact k₂ ↔ k₁ = k₂`-style behavior of a
memoized factory — modeled by `buildArtifact` being an ordinary (referentially
transparent) function: equal arguments give the equal (identical) result.

The patch changes only *which key* reaches the factory:

- post-patch: always `some (config.getD defaultConfig)` — the effective
  configuration (a real string, never the `None` slot);
- pre-patch: the raw argument `config` — which is `none` when omitted.

`implementation_cachedLookup config defaultConfig` corresponds to
`get_resolver(urlconf)` evaluated with `settings.ROOT_URLCONF = defaultConfig`.

## Callee provenance + flag deps

- `buildArtifact` (opaque) ↔ the `lru_cache`-memoized factory
  (`URLResolver(RegexPattern(r'^/'), key)`), an UNCHANGED callee/construction.
  The patch does not alter how the object is built or memoized; it only (a)
  extracts that body under a new name and (b) feeds it the *normalized* key.
  No flag dependency.
- No `axiom buildArtifact_prop` is consumed by the proof:
  `problem_spec_cachedLookup` pins the result to
  `buildArtifact (some (config.getD defaultConfig))` and the impl computes
  exactly that, so `correct_cachedLookup` closes by case analysis on `config` +
  reflexivity. The opaque is declared only so the unchanged memoized factory
  can appear in the executable impl. Hence G-AX has nothing to validate (skip
  stub).

## Why the result is GROUND-able only by the fix (directive 8)

The result is pinned to `buildArtifact` applied to the **normalized** key
`some (config.getD defaultConfig)`. `buildArtifact` is opaque, so the ONLY way
any implementation can produce that exact value is to invoke the factory with
the normalized key — i.e. to perform the normalization the fix introduces. The
pre-patch impl (raw key `config`) produces `buildArtifact config`, which for the
omitted-argument case (`config = none`) is `buildArtifact none`, NOT provably
equal to `buildArtifact (some defaultConfig)` (distinct opaque applications). It
therefore cannot satisfy the spec — exactly the bug.

## G-CONF fuzz seed (pinned)

`seed = 11333` (used by `conformance_check.py`; see that file).
