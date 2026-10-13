#!/usr/bin/env python3
"""G-CONF for django__django-17029.

The gold patch is already applied to /testbed when this runs (so
`Apps.clear_cache` now also calls `self.get_swappable_settings_name.cache_clear()`).
We compare the R/I Python shadow of `implementation_clearCaches` (the Lean impl,
transliterated op-for-op per refinement.md) against the REAL patched
`Apps.clear_cache`, observing the two memoized result caches through their
`functools.cache` `cache_info().currsize`, over >=1e5 fuzzed inputs.
Zero disagreements => exit 0.

Type bijection (mapping.md):
  nameLookupCache : List (String x Option String)
        <-> the entries of Apps.get_swappable_settings_name's functools.cache
            (currsize <-> length)
  entityListCache : List ((Bool x Bool) x List String)
        <-> the entries of Apps.get_models's functools.cache
            (key = (include_auto_created, include_swapped); currsize <-> length)
  ready : Bool                <-> self.ready
  result : CacheRegistry      <-> the cache state after clear_cache()
                                  (both caches emptied; ready unchanged)

We materialize a fuzzed registry cache state on a REAL `Apps` instance by calling
the two cached query methods with a random number of distinct keys (growing each
wrapper's currsize), then run the real patched `clear_cache()` and read back
`currsize` on both wrappers plus `self.ready`. The shadow predicts both currsize
go to 0 and `ready` is unchanged.

stdlib-only; no hypothesis required.
"""
import random
import sys

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=False,
        DATABASES={},
        INSTALLED_APPS=[],
    )
    django.setup()

from django.apps.registry import Apps


def make_registry():
    """A real, populated (empty-installed-apps) Apps registry. populate() runs
    immediately for a non-None installed_apps list, leaving ready == True and
    both functools.cache wrappers empty."""
    return Apps(installed_apps=[])


def populate_caches(a, n_name_keys, n_flag_keys, rng):
    """Fuzz the registry into a cache state by calling the two cached methods
    with distinct arguments. Returns the (pre-clear) observed currsizes for a
    defensive sanity check.

    Note: get_swappable_settings_name internally calls get_models(include_swapped
    =True), so it also contributes to the get_models cache; we account for that
    only as a lower bound and don't assert exact pre-clear sizes."""
    # entity-list cache: keys are (include_auto_created, include_swapped) bools.
    flag_space = [(False, False), (False, True), (True, False), (True, True)]
    for fa, fs in flag_space[:n_flag_keys]:
        a.get_models(include_auto_created=fa, include_swapped=fs)
    # name-lookup cache: distinct query strings.
    for i in range(n_name_keys):
        a.get_swappable_settings_name("conf%d_%d" % (i, rng.randint(0, 1 << 30)))


def oracle(n_name_keys, n_flag_keys, rng):
    """Real patched behavior: build a registry, populate both caches, capture
    `ready`, run the real clear_cache(), then read back both caches' currsize and
    `ready`. Returns (name_currsize_after, entity_currsize_after, ready_after)."""
    a = make_registry()
    ready_before = a.ready
    populate_caches(a, n_name_keys, n_flag_keys, rng)
    a.clear_cache()
    name_after = a.get_swappable_settings_name.cache_info().currsize
    entity_after = a.get_models.cache_info().currsize
    return (name_after, entity_after, a.ready, ready_before)


def shadow(ready_before):
    """R/I transliteration of implementation_clearCaches (Lean):
        s := { s with nameLookupCache := [] }   -> name cache emptied (currsize 0)
        s := { s with entityListCache := [] }   -> entity cache emptied (currsize 0)
        the readiness-gated metadata refresh is the identity on the carrier
    Returns (name_currsize, entity_currsize, ready)."""
    return (0, 0, ready_before)


def main():
    rng = random.Random(17029)  # pinned seed (mapping.md)
    N = 100_000
    disagreements = 0
    first = None
    for i in range(N):
        n_name_keys = rng.randint(0, 6)
        n_flag_keys = rng.randint(0, 4)
        name_after, entity_after, ready_after, ready_before = oracle(
            n_name_keys, n_flag_keys, rng)
        s_name, s_entity, s_ready = shadow(ready_before)
        if (name_after, entity_after, ready_after) != (s_name, s_entity, s_ready):
            disagreements += 1
            if first is None:
                first = (n_name_keys, n_flag_keys,
                         (name_after, entity_after, ready_after),
                         (s_name, s_entity, s_ready))
    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements; first=%r"
              % (disagreements, N, first))
        return 1
    print("G-CONF OK: %d inputs, 0 disagreements" % N)
    return 0


if __name__ == "__main__":
    sys.exit(main())
