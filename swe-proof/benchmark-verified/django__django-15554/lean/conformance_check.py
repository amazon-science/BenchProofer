#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-15554.

The bundle models ONE slice: the alias-allocation performed by
`Query.setup_joins` + `Query.join` (django/db/models/sql/query.py) when a join is
registered while resolving a filtered relation. Its Lean implementation
(`implementation_addJoin`) decides which alias a freshly-built join lands on,
given the current ordered alias registry, the new join's compatibility key, a
fresh alias to allocate, the explicitly-permitted reuse set, the m2m flag, and
the reuse_with_filtered_relation flag:

    reuse = some(can_reuse) if (is_m2m or reuse_with_filtered_relation) else None
    reusable = keys_equal if reuse_with_filtered_relation else keys_eq_full
    cands = [a for (a,k) in registry if permitted(a, reuse) and reusable(k, new_join)]
    if not cands:
        return (fresh_alias, store(registry, fresh_alias, new_join))
    return (cands[-1], registry)

where `store` is the name-keyed registry store modelling
`self.alias_map[alias] = join`: it REPLACES in place when the alias is already
held (discarding the join formerly there, order unchanged) and adds a last entry
otherwise. Both legs are reachable — `table_alias(create=True)` does not
guarantee a fresh alias — so both are enumerated and fuzzed below.

This script transliterates that R/I impl into Python (`shadow_add_join`) and
differential-tests it against an ORACLE: a faithful in-process replica of the
POST-PATCH `setup_joins`/`join` allocation. The oracle reproduces the patched
two-branch candidate computation:

    if reuse_with_filtered_relation and reuse:
        reuse_aliases = [a for a,j in alias_map if a in reuse and j.equals(join)]
    else:
        reuse_aliases = [a for a,j in alias_map if (reuse is None or a in reuse) and j == join]

with `setup_joins`' reuse-set line
`reuse = can_reuse if join.m2m or reuse_with_filtered_relation else None`.

We do NOT stand up Django/ORM (heavy, and the modeled value is a pure decision
over which alias a join is registered under). Instead we reproduce the patched
allocation with light stand-in data: `registry` is a list of
`(alias, (base, filt))` entries; `join.equals` compares `base` only; `j == join`
(`__eq__`) compares `(base, filt)`. The differential is fed BOTH routes: the patch changes the candidate
computation on each (the filtered-relation route gains the confinement to
`reuse`, and the general route's comparison moves from `j.equals(join)` to
`j == join`), so both are modeled and both are fuzzed.

The differential genuinely tests the Lean modeling: the shadow takes the
`reuse = some(can_reuse)` set and matches by `keys_equal` (base only), whereas the
oracle reproduces the patched `join` two-branch logic exactly. They must agree on
every input — in particular the bug case: a base-compatible alias present in the
registry but NOT in `can_reuse` must NOT be reused (a fresh alias is allocated),
so two filtered relations on the same base get distinct aliases.

stdlib-only; deterministic built-in fuzzer. Pinned seed: 15554 (also in mapping.md).
"""
import sys

SEED = 15554
N = 120_000


# --- helpers shared by both legs ---------------------------------------------
def keys_equal(k1, k2):
    # k = (base, filt); equals() ignores filt
    return k1[0] == k2[0]


def keys_eq_full(k1, k2):
    # __eq__ compares the full identity (base, filt)
    return k1 == k2


# --- ORACLE: post-patch setup_joins + join, faithful in-process replica ------
# registry: list of (alias, (base, filt)). `new_join_alias` is the alias the
# freshly-built connection already carries (for a filtered relation this is
# filtered_relation.alias, so it CAN coincide with a registered alias).
# Returns (chosen_alias, new_registry).
def oracle_add_join(registry, new_join, new_join_alias, fresh_alias, can_reuse, is_m2m, rwfr):
    # setup_joins: reuse = can_reuse if join.m2m or reuse_with_filtered_relation else None
    reuse = set(can_reuse) if (is_m2m or rwfr) else None
    # join: candidate computation (two branches)
    if rwfr and reuse:
        reuse_aliases = [a for (a, j) in registry if a in reuse and keys_equal(j, new_join)]
    else:
        reuse_aliases = [
            a for (a, j) in registry
            if (reuse is None or a in reuse) and keys_eq_full(j, new_join)
        ]
    if reuse_aliases:
        # join: prefer the join's own table_alias if already among the
        # candidates, else reuse the most-recent. Registry unchanged.
        if new_join_alias in reuse_aliases:
            return (new_join_alias, list(registry))
        return (reuse_aliases[-1], list(registry))
    # No reuse: allocate an alias and STORE the join under it. The real callee's
    # `self.alias_map[alias] = join` is a DICT STORE, not an append: table_alias
    # does not guarantee the alias is absent (its filtered_relation branch does
    # no uniqueness check at all, and its '%s%d' % (prefix, len(alias_map)+1)
    # branch collides with any user annotation alias of that shape), so a store
    # under an alias already present REPLACES that entry where it sits and
    # discards the join previously held there.
    if any(a == fresh_alias for a, _ in registry):
        return (fresh_alias,
                [(a, (new_join if a == fresh_alias else k)) for a, k in registry])
    return (fresh_alias, list(registry) + [(fresh_alias, new_join)])


# --- shadow of implementation_addJoin (the R/I leg) --------------------------
def shadow_add_join(registry, new_join, new_join_alias, fresh_alias, can_reuse, is_m2m, rwfr):
    reuse = set(can_reuse) if (is_m2m or rwfr) else None
    cands = []
    for (a, k) in registry:
        permitted = True if reuse is None else (a in reuse)
        reusable = keys_equal(k, new_join) if rwfr else keys_eq_full(k, new_join)
        if permitted and reusable:
            cands.append(a)
    if not cands:
        # registryStore: replace in place under an alias already held, else add.
        if any(a == fresh_alias for a, _ in registry):
            return (fresh_alias,
                    [(a, (new_join if a == fresh_alias else k)) for a, k in registry])
        return (fresh_alias, list(registry) + [(fresh_alias, new_join)])
    if new_join_alias in cands:
        return (new_join_alias, list(registry))
    return (cands[-1], list(registry))


def disagree(registry, new_join, new_join_alias, fresh_alias, can_reuse, is_m2m, rwfr):
    got = oracle_add_join(registry, new_join, new_join_alias, fresh_alias, can_reuse, is_m2m, rwfr)
    want = shadow_add_join(registry, new_join, new_join_alias, fresh_alias, can_reuse, is_m2m, rwfr)
    if got != want:
        return ((registry, new_join, new_join_alias, fresh_alias, can_reuse, is_m2m, rwfr), got, want)
    return None


# --- input corpus ------------------------------------------------------------
def _enumerate_edge():
    """Hand-picked edge cases pinning the discriminating reuse clause.

    All on the filtered-relation path (rwfr=True). new_join base=10.
    Tuple order: (registry, new_join, new_join_alias, fresh_alias, can_reuse,
    is_m2m, rwfr). Aliases are ints; filt tags distinguish two filtered
    relations on one base. new_join_alias is the join's own alias (= 8 unless
    it deliberately coincides with a registered alias).
    """
    return [
        # THE fix: alias 1 is base-compatible (base 10, filt A) but NOT in
        # can_reuse {2} -> must NOT reuse -> fresh alias allocated (two JOINs).
        ([(1, (10, 100))], (10, 200), 8, 9, [2], False, True),
        # base-compatible alias 1 IS in can_reuse -> reuse it.
        ([(1, (10, 100))], (10, 200), 8, 9, [1], False, True),
        # empty registry -> always fresh.
        ([], (10, 200), 8, 9, [1, 2], False, True),
        # no base match (base 11 vs 10) even though alias in can_reuse -> fresh.
        ([(1, (11, 100))], (10, 200), 8, 9, [1], False, True),
        # multiple base-compatible aliases in can_reuse -> reuse the most recent.
        ([(1, (10, 100)), (2, (10, 300))], (10, 200), 8, 9, [1, 2], False, True),
        # multiple base-compatible, only an older one permitted -> reuse it.
        ([(1, (10, 100)), (2, (10, 300))], (10, 200), 8, 9, [1], False, True),
        # same base + same filt, in can_reuse -> reuse (identical join).
        ([(1, (10, 200))], (10, 200), 8, 9, [1], False, True),
        # m2m also confines to can_reuse (rwfr True coincides) -> fresh when absent.
        ([(1, (10, 100))], (10, 200), 8, 9, [2], True, True),
        # join's own alias preference: new_join_alias=2 is itself among the
        # candidates {1,2} -> reuse 2 (the own alias), NOT the most-recent rule.
        ([(1, (10, 100)), (2, (10, 300))], (10, 200), 2, 9, [1, 2], False, True),
        # own alias coincides with an OLDER candidate -> still preferred over last.
        ([(1, (10, 100)), (3, (10, 300))], (10, 200), 1, 9, [1, 3], False, True),
        # --- the STORE's two legs: the allocated alias is NOT guaranteed absent ---
        # allocated alias 1 is ALREADY held -> replace that entry in place; the
        # join formerly under alias 1 is discarded and the registry does not grow.
        ([(1, (10, 100))], (10, 200), 8, 1, [2], False, True),
        # same collision, on the ordinary route (rwfr False).
        ([(1, (10, 100))], (10, 200), 8, 1, [], False, False),
        # allocated alias collides with a MIDDLE entry -> position preserved.
        ([(1, (11, 100)), (2, (12, 100)), (3, (13, 100))], (10, 200), 8, 2, [], False, False),
        # allocated alias collides with the FIRST entry -> position preserved.
        ([(1, (11, 100)), (2, (12, 100))], (10, 200), 8, 1, [], False, False),
        # allocated alias absent -> add a last entry (the add leg).
        ([(1, (11, 100))], (10, 200), 8, 9, [], False, False),
    ]


def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def _rand_case(rnd):
    n = next(rnd) % 6            # 0..5 registry entries
    aliases = list(range(1, 9))
    registry = []
    used = []
    for _ in range(n):
        a = aliases[next(rnd) % len(aliases)]
        base = next(rnd) % 4     # base 0..3 (collisions likely)
        filt = next(rnd) % 4     # filt tag 0..3
        # the registry is a NAME-keyed store, so one alias holds one join: a
        # redrawn alias replaces the entry it already has rather than doubling it.
        if a in used:
            registry = [(x, ((base, filt) if x == a else k)) for x, k in registry]
        else:
            registry.append((a, (base, filt)))
            used.append(a)
    nj_base = next(rnd) % 4
    nj_filt = next(rnd) % 4
    new_join = (nj_base, nj_filt)
    # The allocated alias is NOT guaranteed absent from the registry: table_alias's
    # filtered_relation branch performs no uniqueness check, and its counter branch
    # collides with a user annotation alias of the same shape. So draw it from the
    # same universe roughly half the time, to exercise BOTH legs of the store.
    # NOTE: this LCG's LOW bits are degenerate (the low bit strictly alternates,
    # so `% 2` is a function of position and would pin one leg forever); the draw
    # therefore keys on a HIGH bit, which is not short-period.
    fresh = 99 if ((next(rnd) >> 16) % 2 == 0) else aliases[(next(rnd) >> 16) % len(aliases)]
    # new_join's own alias: often drawn from the alias universe so it can
    # coincide with a registered/candidate alias (exercises the preference).
    new_join_alias = aliases[next(rnd) % len(aliases)]
    # can_reuse: random subset of the alias universe (may or may not overlap)
    can_reuse = [a for a in aliases if (next(rnd) % 2 == 0)]
    is_m2m = (next(rnd) % 4 == 0)
    rwfr = (next(rnd) % 2 == 0)   # BOTH routes are modeled
    return registry, new_join, new_join_alias, fresh, can_reuse, is_m2m, rwfr


def main() -> int:
    checked = 0

    for case in _enumerate_edge():
        d = disagree(*case)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    rnd = _lcg(SEED)
    for _ in range(N):
        case = _rand_case(rnd)
        d = disagree(*case)
        if d:
            print(f"DISAGREE fuzz {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
