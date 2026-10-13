#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15569 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo types (dict[str,*]), via the
              mapping.md bijection. The store mutation `eraseKey registry name`
              (I) becomes a dict key delete; the re-derivation of the cached
              view is the A-reference, so it is run as the REAL callee
              `get_lookups()` (NOT the deep model — the deep model is validated
              separately by axiom_check.py / G-AX). Observable outputs: the
              registry post-state AND the cached view post-state.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `RegisterLookupMixin._unregister_lookup` applied at base_commit
              (the real correctness oracle, G-RESOLVE), observed via the owned
              `class_lookups` (registry) and `get_lookups()` (the read-through
              view callers actually consult — this is what the added
              `_clear_cached_lookups()` keeps fresh).

They must agree on every Requires-satisfying input (the removed `name` must be
bound in the registry). Exit 0 iff zero disagreements; any disagreement is a
mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image, gold patch applied),
stdlib + django only. The fuzz seed is pinned (mapping.md §4).
"""
import random
import sys

SEED = 15569
N_FUZZ = 100_000


def _ensure_settings():
    try:
        from django.conf import settings
        if not settings.configured:
            settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[])
    except Exception:
        pass


def main():
    _ensure_settings()
    from django.db.models.query_utils import RegisterLookupMixin

    class Parent(RegisterLookupMixin):
        pass

    class Child(Parent):
        pass

    def view_of(registry):
        """Real read-through view get_lookups() recomputed from a given owned
        registry (inherited layer held fixed in Parent.class_lookups)."""
        Child.class_lookups = dict(registry)
        Child._clear_cached_lookups()
        return dict(Child.get_lookups())

    def oracle(inherited, registry, name):
        """patch.diff behaviour: the patched _unregister_lookup mutates the owned
        store and (added line) re-syncs the cached view. Observe both."""
        Parent.class_lookups = dict(inherited)
        Child.class_lookups = dict(registry)
        Child._clear_cached_lookups()
        # prime the cache with the PRE-removal view, so a missing cache-clear in
        # the operation would leave a stale view observable (the actual bug).
        _ = Child.get_lookups()
        # pass lookup_name explicitly (lookup arg unused on this path), so the
        # op is `del class_lookups[name]; _clear_cached_lookups()`.
        Child._unregister_lookup(None, name)                # REAL patched op
        return dict(Child.class_lookups), dict(Child.get_lookups())

    def shadow(inherited, registry, name):
        """R/I transliteration: eraseKey (I) = dict delete; cached view re-derived
        via the REAL get_lookups() (A-reference). Inherited layer fixed."""
        Parent.class_lookups = dict(inherited)
        reg_post = dict(registry)
        del reg_post[name]                                   # eraseKey (I)
        view_post = view_of(reg_post)                        # A-reference callee
        return reg_post, view_post

    def gen_inputs(n, rng):
        keypool = ["exactly", "exact", "isnull", "iexact", "contains",
                   "my_transform", "gt", "lt", "in", "range", "year",
                   "week_day", "regex", "trunc"]
        # boundary cases first (require: removed name bound in registry)
        boundary = [
            ({}, {"exactly": 1}, "exactly"),                 # registry only, sole key
            ({"exactly": 7}, {"exactly": 1}, "exactly"),     # owned shadows inherited; remove owned -> inherited resurfaces
            ({"isnull": 2}, {"exactly": 1}, "exactly"),      # disjoint inherited remains
            ({"my_transform": 5}, {"my_transform": 99}, "my_transform"),  # F2P shape
            ({}, {"a": 1, "b": 2, "c": 3}, "b"),             # remove a middle key
            ({"a": 1}, {"a": 9, "b": 2}, "a"),               # remove shadowing owned key
            ({"a": 1, "b": 2}, {"c": 3, "d": 4}, "c"),
        ]
        for it in boundary:
            yield it
        for _ in range(n):
            kset = rng.sample(keypool, rng.randint(1, len(keypool)))
            inherited, registry = {}, {}
            for k in kset:
                r = rng.random()
                if r < 0.4:
                    inherited[k] = rng.randint(0, 1000)
                elif r < 0.7:
                    registry[k] = rng.randint(0, 1000)
                else:
                    inherited[k] = rng.randint(0, 1000)
                    registry[k] = rng.randint(0, 1000)
            if not registry:                                  # require: name in registry
                registry[kset[0]] = rng.randint(0, 1000)
            name = rng.choice(list(registry.keys()))
            yield inherited, registry, name

    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for inherited, registry, name in gen_inputs(N_FUZZ, rng):
        count += 1
        sh = shadow(inherited, dict(registry), name)
        orc = oracle(inherited, dict(registry), name)
        if sh != orc:
            disagreements.append((inherited, registry, name, sh, orc))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for inh, reg, nm, sh, orc in disagreements:
            print("  inherited=%r registry=%r name=%r\n    shadow=%r\n    oracle=%r"
                  % (inh, reg, nm, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of removeBinding (eraseKey delete + real "
          "get_lookups view) agrees with patch.diff behaviour on %d inputs "
          "(seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
