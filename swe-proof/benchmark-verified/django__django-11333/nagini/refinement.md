# refinement.md — django__django-11333

The operation-by-operation correspondence between `model.py`'s implementation
(the `get_resolver` impl region + the `resolve_selector` pure helper) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (proof uses an axiom's `Ensures`), **A-reference** (a deep model
validated == a real callee by G-AX), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The structural change: hoist the default substitution out of the cached body

Gold hunk (`django/urls/resolvers.py`):
```
-@functools.lru_cache(maxsize=None)
 def get_resolver(urlconf=None):
     if urlconf is None:
         urlconf = settings.ROOT_URLCONF
+    return _get_cached_resolver(urlconf)
+
+
+@functools.lru_cache(maxsize=None)
+def _get_cached_resolver(urlconf=None):
     return URLResolver(RegexPattern(r'^/'), urlconf)
```

The net behaviour: the omitted-means-default substitution
(`if urlconf is None: urlconf = settings.ROOT_URLCONF`) now happens BEFORE the
memoized call, so the `@lru_cache` memo is keyed on the RESOLVED urlconf. The
model collapses the two-function gold into one `get_resolver(cache, selector,
cached, existing, fresh)` whose impl performs the same: resolve first, then look
up / insert in the cache keyed on the resolved value. (The model's single
`cache` parameter is the `_get_cached_resolver` lru_cache memo; resolving before
the lookup is the whole content of the fix. `cached`/`existing` are pre-state
scalars capturing the entry membership/value of the resolved key — proof
scaffolding for the memoization clause, not extra repo data; see §E.)

| # | model.py impl op (`get_resolver`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `selector: Optional[int]` parameter | `urlconf=None` parameter of `get_resolver` | R | `str` urlconf ↔ `int` selector token; `None` ↔ `None` (mapping.md §2). Only equality of urlconf values is observed. |
| A2 | `key = resolve_selector(selector)` (the `@Pure` helper: `default_selector() if selector is None else selector`) | `if urlconf is None: urlconf = settings.ROOT_URLCONF` (now executed in `get_resolver` BEFORE the cached call) | I + R | the omitted-means-default substitution is identical control flow; `settings.ROOT_URLCONF` ↔ `default_selector()` (R, mapping.md §2). The fix is precisely that this runs before the memoized lookup, which `key = resolve_selector(selector)` preceding the `cache` access in the impl reproduces. |
| A3 | `if key in cache: return cache[key]` | the `@lru_cache(maxsize=None)` hit on `_get_cached_resolver(urlconf)`: a previously-seen RESOLVED `urlconf` returns the stored `URLResolver` | R | the `lru_cache` memo ↔ `cache: Dict[int,int]`; a cache HIT returning the stored object ↔ returning the stored identity token (mapping.md §2). `maxsize=None` ⇒ no eviction, so a stored key is always still present. |
| A4 | `cache[key] = fresh; return fresh` | the `@lru_cache` MISS on `_get_cached_resolver(urlconf)`: construct `URLResolver(RegexPattern(r'^/'), urlconf)`, store it under the key, return it | R | constructing a new `URLResolver` and the cache storing it ↔ allocating a `fresh` identity token (distinct from all cached, by the precondition) and inserting it (mapping.md §2). The constructed object's CONTENTS are not observed by the F2P (`assertIs`/`assertIsNot` test identity only), so the construction is abstracted as a fresh token — no callee axiom is needed. |

## B. The companion `base.py` edit is a mechanical follow-on, not a separate behaviour

Gold hunks (`django/urls/base.py`):
```
-from .resolvers import get_ns_resolver, get_resolver
+from .resolvers import _get_cached_resolver, get_ns_resolver, get_resolver
 ...
-    get_resolver.cache_clear()
+    _get_cached_resolver.cache_clear()
```

Moving the `@lru_cache` from `get_resolver` to `_get_cached_resolver` moves the
`.cache_clear()` method from one to the other; `clear_url_caches` must clear the
function that now holds the memo. Under the abstraction both name the SAME cache
object the model's `cache` parameter stands for (mapping.md §1). There is no
behaviour here beyond "the cache populated by the lookup is the cache cleared by
the clear" — which is already implied by there being one `cache`. No model
operation corresponds to it and none is needed; it is not an independently
observable fixed behaviour (so no separate `model_prepatch_<k>`).

## C. No kind-3 (unexpressible-changed-op) steps; no axioms

Every step above is R or I. The operation that genuinely changed — WHERE the
default substitution runs relative to the memo key — is modeled **deeply** (the
ordering `key = resolve_selector(selector)` then the keyed lookup in the impl),
not hidden behind any axiom. There is **no `@ContractOnly` axiom at all**
(neither A-consumed nor A-reference): the `lru_cache` memo is modeled deeply as a
`Dict` lookup-or-insert, and the `URLResolver` construction is abstracted as a
fresh-token allocation because its contents are unobserved by the test. Hence
there is nothing for G-AX to check; soundness rests entirely on the refinement
fidelity audited here (G-EQ) and the real-harness oracle (G-RESOLVE).

## D. verify(model) ⇒ resolved

`get_resolver` verifies only if `Result() == cache[resolve_selector(selector)]`
(A2–A4) — i.e. the handed-back object is the one cached under the RESOLVED
selector, with omitted and default resolving to the same slot. By R (urlconf ↔
selector token, `settings.ROOT_URLCONF` ↔ default, lru_cache memo ↔ `Dict`,
`URLResolver` identity ↔ token) this is exactly what the gold's
"resolve-then-memoize" computes: `get_resolver()` and
`get_resolver(settings.ROOT_URLCONF)` hit one `_get_cached_resolver` entry
(`assertIs`), and a different urlconf hits a different entry (`assertIsNot`). The
pre-patch keys on the raw argument; `model_prepatch.py` reproduces that (key on
a `-1` "no-argument" sentinel when omitted) and **fails** the postcondition
`resolve_selector(selector) in cache` — exactly the spec sensing the change
(G-DIFF). Therefore a model satisfying this spec, refined by the map above, is
the gold patch up to type refinement, and the gold patch resolves (G-RESOLVE).
The only trust point is refinement fidelity (this document, G-EQ); there is no
axiom-soundness trust point because there is no axiom.

## E. Why the memoization clause uses pre-state scalars (`cached`/`existing`)

The memoization guarantee — "a resolved selector already in the cache hands back
its existing object, never a rebuilt one" — is the clause that rejects an impl
which over-constructs (writes `fresh` into an occupied slot). Stating it as
`Implies(resolve_selector(selector) in Old(cache), Result() ==
Old(cache)[resolve_selector(selector)])` was found UNSOUND in Nagini 1.2.0: an
overwrite-on-hit impl (`cache[key] = fresh; return fresh`) VERIFIED against it,
because Nagini does not soundly relate `Old(cache)[k]` to the entry value once
the body has written key `k` (the over-construct adversary slipped through).

The fix mirrors the django-12713 pattern: lift the entry state of the resolved
key into pre-state SCALAR parameters bound by preconditions —
`cached == (resolve_selector(selector) in cache)`,
`Implies(cached, cache[resolve_selector(selector)] == existing)`,
`Implies(cached, existing != fresh)` — and state memoization as
`Implies(cached, Result() == existing)`. Scalars are immune to the Dict-`Old`
gap, so the overwrite-on-hit adversary now fails this clause (verified). The
`cached`/`existing`/`fresh` parameters are proof scaffolding, not new repo data:
under the refinement they are the entry membership, the entry value, and the
freshly-constructed identity of the `_get_cached_resolver` lru_cache memo for the
resolved urlconf — every concrete `get_resolver` invocation supplies exactly one
consistent valuation of them (`maxsize=None` guarantees a never-evicted, single-
valued memo), so a verifying impl is sound for the real call. The clauses that
DO use `Old(cache[k])` (distinctness for OTHER keys, no-key-dropped) are over
keys the body never writes, where the `Old`-read is the standard, sound
frame-preservation form (and the corrupt-other-key adversary is correctly
rejected by it).
