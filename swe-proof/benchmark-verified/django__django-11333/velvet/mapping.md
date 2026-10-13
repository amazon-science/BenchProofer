# mapping.md — django__django-11333

Symbol binding, the Lean ↔ Python type bijection, callee provenance, and the
pinned G-CONF fuzz seed. All locations are at `base_commit`
`55b68de643b5c2d5f0a8ea7587ab3b2966021ccc`.

## 1. Symbol binding

| Lean (`Solution.lean`) | Python (repo @ base_commit) | location |
|---|---|---|
| `method sharedHandle` | `django.urls.resolvers.get_resolver` | `django/urls/resolvers.py:66-70` (the `@functools.lru_cache`-wrapped function the patch splits) |
| `def lookupKey` | the `if urlconf is None: urlconf = settings.ROOT_URLCONF` normalization | `django/urls/resolvers.py:68-69` |
| parameter `requested : Option String` | parameter `urlconf=None` | `django/urls/resolvers.py:67` |
| parameter `ambient : String` | `settings.ROOT_URLCONF` (the default urlconf) | `django/urls/resolvers.py:69` |
| return `out : Option String` | the returned `URLResolver` object, observed by identity | `django/urls/resolvers.py:70` |

### Additional change site (shipped, not modeled)
`django/urls/base.py` — import of `_get_cached_resolver` (line 10) and
`clear_url_caches` swapping `get_resolver.cache_clear()` →
`_get_cached_resolver.cache_clear()` (line 95). This is the mechanical
follow-through of renaming the lru_cached layer; no F2P/P2P test observes it
independently. Shipped verbatim in `patch.diff` for G-RESOLVE. See refinement.md.

## 2. The Lean ↔ Python type bijection (used by G-CONF)

The fix concerns the IDENTITY of the memoized object, not its contents. The
`URLResolver` object is a rich object none of whose touched fields matter here;
the only observable the bug/fix and the F2P test exercise is **object identity**
(`assertIs` / `assertIsNot`). We refine object identity to **memoization-key
equality** — the lru_cache returns one object per distinct key:

| repo reality | model as | bijection |
|---|---|---|
| `urlconf` argument (`None` or a dotted module path `str`) | `Option String` | `None` ↔ `none`; dotted name `s` ↔ `some s` |
| `settings.ROOT_URLCONF` (the default config name, a `str`) | `ambient : String` | identity (a `str` ↔ a Lean `String`) |
| the returned `URLResolver` object, observed by `id(...)` | `out : Option String`, the storage key it carries | object identity ↔ key equality: `id(a)==id(b)` ⟺ `key(a)==key(b)`. A resolver is always produced ⟹ the key is always `some _` (never `none`). |
| the lru_cache key actually used | `lookupKey requested ambient` | `none ↦ ambient`, `some u ↦ u` (the RESOLVED key) |

Why object-identity ⟺ key-equality is a faithful refinement (not a weakening):
`functools.lru_cache(maxsize=None)` is a pure memo table — it returns the *same*
object for *equal* argument keys and a *fresh* object for *each distinct* key.
The patched `get_resolver` computes the key as `lookupKey` (resolve `None` to
`ROOT_URLCONF` first), so equal resolved keys ⟹ same object and distinct
resolved keys ⟹ distinct objects. G-CONF validates BOTH directions against the
real patched callee on fuzzed request pairs, so the refinement cannot silently
over- or under-coalesce.

## 3. Callees and flag dependencies

- **No axiomatized callees; no deep-model references.** `sharedHandle` does not
  delegate to any unchanged callee whose contract the proof consumes. The
  `URLResolver(RegexPattern(r'^/'), urlconf)` construction is an unchanged
  callee, but the patch does NOT change WHAT object is built — only the KEY it
  is cached under — so the construction is irrelevant to the modeled behavior
  and is not axiomatized (directive 7: no dead axioms).
- **No `_populate` triggering.** `URLResolver.__init__`
  (`django/urls/resolvers.py:367`) only stores the dotted `urlconf_name`; it
  imports the urlconf module lazily, inside `_populate`, which neither the F2P
  test's `assertIs`/`assertIsNot` nor `conformance_check.py` ever calls. Hence
  arbitrary dotted-name strings (and the empty string) are safe G-CONF fuzz
  inputs — no module import, no I/O.
- **No flag-dependent callees.**

## 4. G-CONF fuzz seed

`SEED = 11333`, `N_FUZZ = 100_000` request draws plus pinned boundary cases
(`None`; an explicit mention of `ambient`, twice; a non-default name, twice; the
empty string). Inputs are biased toward a small pool so identity collisions are
forced. `settings.ROOT_URLCONF` is set to `"conf_check.root_urlconf"` via
`settings.configure` (the dotted name is never imported, per §3).

## 5. Verifier pins

- Velvet commit: `2cf0acb04c510848e597aa6214b7665fea86319d`
- Lean toolchain: `leanprover/lean4:v4.24.0`
