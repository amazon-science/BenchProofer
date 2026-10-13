# refinement.md — django__django-17029

Maps every operation in `implementation_clearCaches` to its `patch.diff`
counterpart (the patched `Apps.clear_cache`, see mapping.md). Tags: **R**
type-refinement, **A-consumed** proof uses a callee axiom, **A-reference**
deep-modeled changed op validated == real callee, **I** identical concrete op.

## Patch (post-patch)
```python
# django/apps/registry.py — Apps.clear_cache
def clear_cache(self):
    self.get_swappable_settings_name.cache_clear()   # ADDED
    self.get_models.cache_clear()
    if self.ready:
        for app_config in self.app_configs.values():
            for model in app_config.get_models(include_auto_created=True):
                model._meta._expire_cache()
```

## Operation correspondence
| # | Lean op (`implementation_clearCaches`) | patch.diff / governed op | tag | note |
|---|---|---|---|---|
| 1 | `let mut s := st` | bind `self` (the registry whose caches are discarded) | I | establishes the mutable carrier. |
| 2 | `s := { s with nameLookupCache := [] }` | `self.get_swappable_settings_name.cache_clear()` (THE ADDED LINE) | R | `functools.cache.cache_clear()` ↔ emptying the wrapper's memoized-entry list. This is exactly the op the patch introduces; the prepatch omits it. |
| 3 | `s := { s with entityListCache := [] }` | `self.get_models.cache_clear()` | R | same `cache_clear()` ↔ `[]` refinement; present pre- and post-patch. |
| 4 | (return `s`; the `if self.ready:` refresh is a no-op on the carrier) | `if self.ready: … model._meta._expire_cache()` | I | the readiness-gated metadata refresh touches a separate metadata layer (not either result cache) and does not refill the caches; on the modeled carrier it leaves `nameLookupCache`, `entityListCache`, and `ready` unchanged, so it is the identity op. `ready` is only read. |

Every op is R or I; **no A row** (no axiom consumed, no deep-model reference).
Therefore `meta.json axioms = []`, `deep_model_references = []`, and
`axiom_check.py` is a skip stub.

## R/I legs ⇒ G-CONF
The whole impl is R/I, so `conformance_check.py` mechanically differential-tests
the impl shadow (both caches emptied, `ready` preserved) against the real patched
`Apps.clear_cache` behavior observed via `get_swappable_settings_name`/
`get_models`'s `cache_info().currsize` over ≥10^5 fuzzed inputs.
`conf_skip = false`.

## Prepatch = the real bug
`Solution_prepatch.lean` omits op #2 (`nameLookupCache := []`) — exactly the line
the gold patch adds. After `clear_cache()` the name-lookup cache still carries its
input entries, so the carried gold proof fails to typecheck on the discriminating
clause `result.nameLookupCache = []`. This is precisely what the FAIL_TO_PASS
test `test_clear_cache` asserts: after `apps.clear_cache()`,
`get_swappable_settings_name.cache_info().currsize == 0`. The spec is
byte-identical between the two files (only the impl differs).

## patch.diff == gold
`patch.diff` is the gold patch verbatim (the one-line addition to
`Apps.clear_cache`); it applies at `base_commit` and the harness resolves.
