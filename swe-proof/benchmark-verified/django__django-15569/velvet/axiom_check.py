#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-15569.

The bundle's only kind-A leg is an **A-reference**: the deep model
`recomputeLookups` (Solution.lean `pure` region) is claimed equal, as a
key->value mapping, to the REAL read-through derivation the operation defers to
— `RegisterLookupMixin.get_lookups()` (django/db/models/query_utils.py:158,
unchanged by the gold patch), whose body reverse-merges the per-class
`class_lookups` dicts along the MRO so the most-derived class's bindings win.

This script builds a real `RegisterLookupMixin` subclass hierarchy (a parent
contributing the inherited bindings, a child whose `class_lookups` is the owned
registry), populates `class_lookups` from boundary + fuzzed key/value sets,
clears the lru_cache, calls the REAL `get_lookups()`, and asserts

    dict(recomputeLookups(inherited, registry)) == get_lookups()   (as a mapping)

over boundary cases + >=1e5 fuzzed configurations. There is NO consumed axiom to
check (the proof consumes none); this validates the A-reference deep model.

Imports only `django.*` already present in the instance image. Exit 0 iff sound.
"""
import random
import sys


def _ensure_settings():
    """query_utils imports cleanly without settings in this version, but guard
    anyway so the check is robust across import-time changes."""
    try:
        from django.conf import settings
        if not settings.configured:
            settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[])
    except Exception:
        pass


# --- the deep model, transliterated from Solution.lean's pure region ---------
# recomputeLookups inherited registry =
#   registry ++ inherited.filter (fun kv => (lookupKey registry kv.1).isNone)
# as a key->value mapping this is {**inherited, **registry} (registry wins).
def recompute_lookups(inherited, registry):
    out = dict(registry)
    for k, v in inherited.items():
        if k not in registry:
            out[k] = v
    return out


def main():
    _ensure_settings()
    from django.db.models.query_utils import RegisterLookupMixin

    # Real subclass hierarchy: Child's class_lookups is the owned registry;
    # Parent's is the inherited layer. get_lookups() walks inspect.getmro and
    # reverse-merges, so Child (most derived) wins on shared keys.
    class Parent(RegisterLookupMixin):
        pass

    class Child(Parent):
        pass

    def real_get_lookups(inherited, registry):
        Parent.class_lookups = dict(inherited)
        Child.class_lookups = dict(registry)
        # bust the lru_cache for the whole subclass tree, like the gold patch's
        # _clear_cached_lookups, so get_lookups recomputes from current state.
        Child._clear_cached_lookups()
        return dict(Child.get_lookups())

    def check(inherited, registry):
        observed = real_get_lookups(inherited, registry)          # REAL callee
        expected = recompute_lookups(inherited, registry)         # deep model
        # restrict observed to keys our two layers contributed (RegisterLookupMixin
        # / object contribute no class_lookups of their own in this hierarchy).
        assert observed == expected, (
            "recomputeLookups deep model unsound:\n"
            "  inherited=%r registry=%r\n  get_lookups()=%r\n  deep model =%r"
            % (inherited, registry, observed, expected))

    # --- boundary configurations --------------------------------------------
    boundary = [
        ({}, {}),                                   # both empty
        ({}, {"exactly": 1}),                       # owned only
        ({"exactly": 7}, {}),                       # inherited only
        ({"exactly": 7}, {"exactly": 1}),           # owned shadows inherited
        ({"isnull": 2}, {"exactly": 1}),            # disjoint
        ({"isnull": 2, "exact": 3}, {"exactly": 1, "exact": 9}),  # partial overlap
        # F2P shape: a transform/lookup registered then about to be removed
        ({"my_transform": 5}, {"my_transform": 99}),
        ({}, {"a": 1, "b": 2, "c": 3, "d": 4}),
        ({"a": 1, "b": 2, "c": 3}, {"b": 20, "c": 30, "e": 50}),
    ]
    for inh, reg in boundary:
        check(inh, reg)

    # --- randomized fuzz ----------------------------------------------------
    rng = random.Random(15569)
    keypool = ["exactly", "exact", "isnull", "iexact", "contains", "my_transform",
               "gt", "lt", "in", "range", "year", "week_day", "regex", "trunc"]
    N = 100_000
    for _ in range(N):
        kset = rng.sample(keypool, rng.randint(0, len(keypool)))
        inherited, registry = {}, {}
        for k in kset:
            r = rng.random()
            if r < 0.4:
                inherited[k] = rng.randint(0, 1000)
            elif r < 0.7:
                registry[k] = rng.randint(0, 1000)
            else:  # in both -> collision; registry must win
                inherited[k] = rng.randint(0, 1000)
                registry[k] = rng.randint(0, 1000)
        check(inherited, registry)

    print("G-AX OK: recomputeLookups deep model (== get_lookups() reverse-merge, "
          "owned wins) sound on %d boundary + %d fuzz configurations. "
          "No consumed axiom." % (len(boundary), N))
    return 0


if __name__ == "__main__":
    sys.exit(main())
