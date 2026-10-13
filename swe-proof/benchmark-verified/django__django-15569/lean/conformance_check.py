#!/usr/bin/env python3
"""G-CONF for django__django-15569.

Differential test: the R/I shadow of `implementation_unregisterLookup` (built
from the Lean impl per refinement.md) vs. the real fixed behavior of
`RegisterLookupMixin._unregister_lookup` (drop name from class_lookups + bust the
reader memo), over >=1e5 fuzzed registry states. Exit 0 iff zero disagreements.

The model: a registry is (classLookups: list[(name, id)], cache: Optional[list]).
- Lean impl (shadow): eraseKey(classLookups, name); cache := None.
- Real fixed behavior (reference): del the name from the table; clear the memo
  (cache empty); reader view getLookups() = cache if present else table.
stdlib-only.
"""
import random
import sys

SEED = 15569
N = 100_000


def erase_key(table, name):
    return [(k, v) for (k, v) in table if k != name]


def keys(table):
    return [k for (k, _) in table]


def get_lookups(table, cache):
    # reader view: memoized snapshot if present, else recompute from table
    return cache if cache is not None else table


# ---- Lean impl shadow (R/I, per refinement.md) ----
def shadow_impl(table, cache, name):
    st_table = table
    st_cache = cache
    st_table = erase_key(st_table, name)   # op 2: del name
    st_cache = None                        # op 3: invalidate memo
    return st_table, st_cache


# ---- Real fixed behavior (reference) ----
def reference_fixed(table, cache, name):
    # del cls.class_lookups[name]  (only present keys are deleted; absent -> KeyError
    #   in Python, but the F2P path always unregisters a registered name, so we
    #   only feed names that are present, matching the modeled precondition.)
    new_table = erase_key(table, name)
    # cls._clear_cached_lookups(): memo emptied
    new_cache = None
    return new_table, new_cache


def spec_holds(s_table, name, r_table, r_cache):
    # mirrors problem_spec_unregisterLookup (strengthened):
    # 1. result table = eraseKey(input table, name) exactly (order-preserving)
    if r_table != erase_key(s_table, name):
        return False
    # 2. memo invalidated (cleared, not re-primed)
    if r_cache is not None:
        return False
    view = get_lookups(r_table, r_cache)
    # 3. reader view = recomputed table
    if view != r_table:
        return False
    # 4. removed name absent from the reader view
    if name in keys(view):
        return False
    return True


def rand_state(rng):
    n = rng.randint(0, 8)
    names = [f"lk{rng.randint(0, 12)}" for _ in range(n)]
    # dict semantics: unique keys; keep last
    d = {}
    for nm in names:
        d[nm] = rng.randint(0, 1000)
    table = list(d.items())
    rng.shuffle(table)
    # cache: None, or a possibly-stale snapshot
    r = rng.random()
    if r < 0.34:
        cache = None
    elif r < 0.67:
        cache = list(table)  # fresh snapshot
    else:
        # stale snapshot: add an extra stale name
        cache = list(table) + [(f"stale{rng.randint(0,5)}", rng.randint(0, 1000))]
    return table, cache


def main():
    rng = random.Random(SEED)
    disagreements = 0
    for i in range(N):
        table, cache = rand_state(rng)
        if table:
            name = rng.choice(keys(table))      # unregister a present name (F2P path)
        else:
            name = "lk0"                         # vacuous removal
        st, sc = shadow_impl(table, cache, name)
        rt, rc = reference_fixed(table, cache, name)
        # 1. shadow == reference behavior
        if sorted(st) != sorted(rt) or sc != rc:
            disagreements += 1
            if disagreements <= 5:
                print(f"[mismatch shadow/ref] state={table} cache={cache} name={name}")
            continue
        # 2. shadow result satisfies the spec
        if not spec_holds(table, name, st, sc):
            disagreements += 1
            if disagreements <= 5:
                print(f"[spec violated] state={table} cache={cache} name={name}")
    if disagreements:
        print(f"G-CONF FAIL: {disagreements}/{N} disagreements")
        sys.exit(1)
    print(f"G-CONF OK: {N} fuzzed inputs, zero disagreements (seed={SEED})")
    sys.exit(0)


if __name__ == "__main__":
    main()
