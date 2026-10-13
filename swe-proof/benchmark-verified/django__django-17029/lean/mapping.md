# mapping.md — django__django-17029

## Instance
- repo: django/django
- base_commit: 953f29f700a60fc09b08b2c2270c12c447490c6a
- spec_provenance: cold (derived from problem_statement + gold patch + base-commit
  source only)

## The logical change
The gold patch adds ONE line to `Apps.clear_cache` in
`django/apps/registry.py`:

```python
def clear_cache(self):
    """
    Clear all internal caches, for methods that alter the app registry.
    This is mostly used in tests.
    """
    self.get_swappable_settings_name.cache_clear()   # <-- ADDED by the patch
    # Call expire cache on each model. ...
    self.get_models.cache_clear()
    if self.ready:
        for app_config in self.app_configs.values():
            for model in app_config.get_models(include_auto_created=True):
                model._meta._expire_cache()
```

`Apps` memoizes TWO independent query methods, each decorated with
`@functools.cache` (a `functools._lru_cache_wrapper`):

```python
@functools.cache
def get_models(self, include_auto_created=False, include_swapped=False): ...   # registry.py:168

@functools.cache
def get_swappable_settings_name(self, to_string): ...                          # registry.py:283
```

Each wrapper holds its own result cache keyed by the call's arguments. Pre-patch
`clear_cache` calls `self.get_models.cache_clear()` but NOT
`self.get_swappable_settings_name.cache_clear()`, so the latter's memoized
answers survive a `clear_cache()` — the bug. The F2P test
`test_clear_cache` populates both caches, calls `clear_cache()`, and asserts
`get_swappable_settings_name.cache_info().currsize == 0` AND
`get_models.cache_info().currsize == 0`.

The `if self.ready:` block performs an auxiliary per-entity metadata refresh
(`model._meta._expire_cache()`); it touches a separate metadata layer, not the
two `functools.cache` result caches, and does not refill them (the comment in
source notes it circumvents `self.get_models()` precisely to avoid refilling the
cache while cloning). `self.ready` is only read.

## Modeled function
I model `Apps.clear_cache` as a total function on the registry's cache state.
The smallest carrier whose observable behavior the patch changes is the pair of
memoized result caches plus the readiness flag. Each `functools.cache` wrapper
is modeled as the list of its memoized key/value entries; `cache_clear()` empties
that list; `cache_info().currsize` is the entry count. The patch's observable
effect is purely on the post-`clear_cache` cache contents, which is what the
model and F2P test pin.

## Symbol binding
| Lean symbol | Python source @ base_commit |
|---|---|
| `implementation_clearCaches` | `Apps.clear_cache` (`django/apps/registry.py:370`) |
| `problem_spec_clearCaches` | the post-condition the registry's cache state must satisfy after `clear_cache()` |
| `CacheRegistry.nameLookupCache` | the memoized result cache of `Apps.get_swappable_settings_name` (`@functools.cache`, registry.py:283) |
| `CacheRegistry.entityListCache` | the memoized result cache of `Apps.get_models` (`@functools.cache`, registry.py:168) |
| `CacheRegistry.ready` | `self.ready` (registry.py:43), the readiness flag gating the metadata refresh |

## Type bijection (Lean ↔ Python) — used by G-CONF / G-AX
| Lean | Python | notes |
|---|---|---|
| `nameLookupCache : List (String × Option String)` | `get_swappable_settings_name`'s `functools.cache` entries | each entry = `(to_string_arg, returned_settings_name_or_None)`; `none ↔ None`, `some n ↔ str n`. `currsize ↔ length`. |
| `entityListCache : List ((Bool × Bool) × List String)` | `get_models`'s `functools.cache` entries | key = `(include_auto_created, include_swapped)`; value = list of selected entity (model) names. `currsize ↔ length`. |
| `ready : Bool` | `self.ready` | identity |
| result `: CacheRegistry` | the registry's cache state after `clear_cache()` | both caches emptied; `ready` unchanged |

`functools.cache.cache_clear()` ↔ setting the corresponding entry list to `[]`;
`cache_info().currsize == 0` ↔ that list being `[]`.

## Callee provenance / flag deps
- No unchanged repo callee is consumed. The two `cache_clear()` calls are
  modeled directly as emptying the corresponding entry lists, and the
  `if self.ready:` metadata-refresh block is a no-op on the modeled carrier
  (it touches a separate metadata layer, never the two result caches). There is
  no `opaque` callee and no `axiom <callee>_prop`; the `axioms` region is empty
  and `axiom_check.py` is a skip stub.
- No flag dependency on the discard path: `clear_cache` unconditionally clears
  both caches regardless of `self.ready`; `ready` only gates the unrelated
  metadata refresh.

## G-CONF fuzz seed
- pinned seed: `17029`
- ≥10^5 fuzzed registry cache states (random name-lookup and entity-list entries
  of varying sizes, random `ready`); the shadow of `implementation_clearCaches`
  is compared against the real patched `Apps.clear_cache` behavior observed
  through `cache_info().currsize` on both wrappers.
