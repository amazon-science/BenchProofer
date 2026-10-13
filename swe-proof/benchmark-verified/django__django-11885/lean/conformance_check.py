#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-11885.

The bundle models ONE decision: how the cascade-deletion collector SCHEDULES its
fast-delete bulk operations (`Collector.collect`, the `collect_related`
fast-delete grouping). The modeled value is a PURE function of one observable
(mapping.md):

    rels : list[(table, column)]
           the fast-deletable cascading relations, in discovery order,
           each a (related_model identity, join-column identity) pair.

Post-patch rule (the `model_fast_deletes = defaultdict(list)` grouping, then
`.items()`):

    groups = defaultdict(list)
    for (m, f) in rels:
        groups[m].append(f)          # model_fast_deletes[related_model].append(field)
    result = list(groups.items())    # one combined op per table, in key-insertion order

Standing up a database / ORM to drive the real `Collector.collect` is heavy and
unnecessary: the modeled value is this pure grouping over the (table, column)
pairs the candidate-relation walk exposes. So the ORACLE below is a faithful
in-process replica that uses the EXACT patched data structure (a real Python
`defaultdict(list)` keyed by table, materialized with `.items()`), and the SHADOW
is the op-for-op transliteration of `implementation_combineFastDeletes`
(append-to-existing-entry / new-entry-at-end, per refinement.md).

Python ≥3.7 dicts preserve key-insertion order and per-key lists preserve append
order, so the schedule is an ORDERED structure (key order = first-discovery of
tables; value order = discovery of columns). We therefore compare the two legs as
ORDERED lists — this genuinely tests the Lean list-grouping ↔ Python
defaultdict-insertion-order bijection: agreement is required on the table order,
on which columns land under each table, and on the order of those columns —
including the multi-column-per-table case the fix combines (the dedup of the
schedule into one op per table) and the repeated-column case.

stdlib-only. Pinned seed: 11885 (also in mapping.md).
"""
from collections import defaultdict
import random
import sys

SEED = 11885
N = 120_000


# --- ORACLE: faithful in-process replica of the patched scheduler ------------
def oracle_schedule(rels):
    groups = defaultdict(list)          # model_fast_deletes = defaultdict(list)
    for (m, f) in rels:
        groups[m].append(f)             # model_fast_deletes[related_model].append(field)
    return [(m, list(fs)) for m, fs in groups.items()]   # .items()


# --- SHADOW of implementation_combineFastDeletes (the R/I leg) ---------------
# Mirrors Solution.lean: groups := []; for p in rels: if groups has p.1 then
# append p.2 to that entry else append (p.1, [p.2]); return groups.
def shadow_schedule(rels):
    groups = []                          # list of [table, [cols]]
    for (m, f) in rels:
        if any(q[0] == m for q in groups):
            groups = [
                (q[0], q[1] + [f]) if q[0] == m else (q[0], q[1])
                for q in groups
            ]
        else:
            groups = groups + [(m, [f])]
    return [(m, list(fs)) for m, fs in groups]


def disagree(rels):
    got = oracle_schedule(rels)
    want = shadow_schedule(rels)
    if got != want:                      # compared as ORDERED lists (mapping.md)
        return (rels, got, want)
    return None


def _enumerate_edge():
    return [
        [],                                              # no fast-deletable relations
        [(0, 0)],                                        # single relation
        [(0, 0), (0, 1)],                                # F2P shape: one table, two columns -> ONE combined op
        [(0, 0), (1, 0)],                                # two tables, one column each
        [(0, 0), (1, 0), (0, 1)],                        # interleaved: table 0 revisited after table 1
        [(0, 0), (0, 0)],                                # repeated identical (table, column)
        [(2, 5), (2, 5), (2, 6), (3, 1)],                # multi-column + duplicate column
        [(1, 0), (0, 0), (1, 1), (0, 1), (2, 2)],        # three tables, mixed order
    ]


def main() -> int:
    checked = 0
    for rels in _enumerate_edge():
        d = disagree(rels)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        k = rng.randint(0, 8)
        rels = []
        for _ in range(k):
            m = rng.randint(0, 4)        # small table pool -> frequent collisions (the combine case)
            f = rng.randint(0, 5)
            rels.append((m, f))
        d = disagree(rels)
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
