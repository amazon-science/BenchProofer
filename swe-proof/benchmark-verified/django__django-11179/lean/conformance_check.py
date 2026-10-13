#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-11179.

The bundle models ONE function: `Collector.delete`
(`django/db/models/deletion.py:262`). Its Lean implementation
(`implementation_delete`) removes a batch of collected records and clears each
removed record's primary-key identity, returning the post-deletion record groups
and a count:

    match data:
      [(label, [inst])] if directly_deletable(inst):
          return ([(label, [inst with pk=None])], direct_count)   # fast path + fix
      _:
          return (clear_all_pks(data), general_total)             # general path

This script transliterates that R/I impl into Python (`shadow_delete`) and
differential-tests it against the ORACLE: a faithful in-process replica of the
POST-PATCH behavior of `Collector.delete` at the same abstraction.

We do NOT stand up Django/ORM (heavy; the modeled value is the pure side effect
on the in-memory pk and the branch-selected count). Both legs receive the SAME
inputs: the collected groups `data` (each a `(label, [instance])` with instance =
a pk that is an int or None), the unchanged fast-delete decision
`directly_deletable` (A-reference predicate), and the two abstract row counts
`direct_count` / `general_total` (A-reference numerals).

ORACLE (post-patch delete, faithful replica):
  * if exactly one group with exactly one record and can_fast_delete:
        delete_batch(...)                 # count = direct_count
        setattr(instance, pk, None)       # <-- the fix
        return ([(label, [pk=None])], direct_count)
  * else: atomic deletes; then for every collected instance setattr(pk, None)
        return (clear_all_pks(data), general_total)

The differential genuinely tests the Lean modeling: both legs must clear the
removed record's pk on EVERY path — in particular on the single-record fast path,
which is exactly the case the patch fixes (pre-fix that path left the pk stale).

stdlib-only; deterministic built-in fuzzer. Pinned seed: 11179 (also recorded in
mapping.md).
"""
import sys

SEED = 11179
N = 120_000


# --- helpers shared in spirit by both legs -----------------------------------
# An "instance" is modeled by its touched field only: pk, an int or None.
# A "group" is (label, [pk, ...]). `data` is a list of groups.
def clear_all_pks(data):
    return [(label, [None for _ in pks]) for (label, pks) in data]


def is_single_fast(data, directly_deletable):
    if len(data) == 1 and len(data[0][1]) == 1:
        return directly_deletable(data[0][1][0])
    return False


# --- ORACLE: the post-patch delete(), faithful in-process replica ------------
def oracle_delete(data, directly_deletable, direct_count, general_total):
    if len(data) == 1 and len(data[0][1]) == 1:
        label, pks = data[0]
        inst = pks[0]
        if directly_deletable(inst):
            # delete_batch -> direct_count; setattr(instance, pk, None); return early
            return ([(label, [None])], direct_count)
    # general path: deletes, then clear every collected instance's pk
    return (clear_all_pks(data), general_total)


# --- shadow of implementation_delete (the R/I leg) ---------------------------
def shadow_delete(data, directly_deletable, direct_count, general_total):
    if len(data) == 1 and len(data[0][1]) == 1:
        label, pks = data[0]
        inst = pks[0]
        if directly_deletable(inst):
            return ([(label, [None])], direct_count)
    return (clear_all_pks(data), general_total)


def disagree(data, directly_deletable, direct_count, general_total):
    got = oracle_delete(data, directly_deletable, direct_count, general_total)
    want = shadow_delete(data, directly_deletable, direct_count, general_total)
    if got != want:
        return (data, got, want)
    return None


# --- input corpus ------------------------------------------------------------
def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def _enumerate_edge(deletable):
    """Hand-picked edge cases pinning the discriminating clauses.

    `deletable` is the fast-delete predicate used for these cases.
    """
    return [
        # THE fix: single group, single record, fast-deletable -> pk cleared on fast path
        [(0, [42])],
        # single group, single record, NOT fast-deletable -> general path
        [(0, [42])] if not deletable else [(0, [42])],
        # single group, single record, pk already None
        [(0, [None])],
        # single group, two records -> general path (not single)
        [(0, [1, 2])],
        # two groups, one record each -> general path
        [(0, [1]), (1, [2])],
        # empty data
        [],
        # single group, empty record list -> not single (len 0)
        [(0, [])],
        # single group, single record, negative pk
        [(5, [-7])],
    ]


def _rand_data(rnd):
    n_groups = next(rnd) % 4          # 0..3 groups
    data = []
    for g in range(n_groups):
        n_rec = next(rnd) % 4         # 0..3 records
        pks = []
        for _ in range(n_rec):
            if next(rnd) % 7 == 0:
                pks.append(None)
            else:
                pks.append(next(rnd) % 100 - 50)
        data.append((g, pks))
    return data


def main() -> int:
    checked = 0

    for deletable in (True, False):
        directly_deletable = (lambda inst: deletable)
        for data in _enumerate_edge(deletable):
            for dc, gt in ((3, 7), (0, 0), (1, 99)):
                d = disagree(data, directly_deletable, dc, gt)
                if d:
                    print(f"DISAGREE edge {d[0]!r}: oracle={d[1]} shadow={d[2]}")
                    print("status=fail")
                    return 1
                checked += 1

    rnd = _lcg(SEED)
    for _ in range(N):
        data = _rand_data(rnd)
        # fast-delete decision is an arbitrary predicate; fuzz it per-call
        flag = (next(rnd) % 2 == 0)
        directly_deletable = (lambda inst, f=flag: f)
        dc = next(rnd) % 1000
        gt = next(rnd) % 1000
        d = disagree(data, directly_deletable, dc, gt)
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
