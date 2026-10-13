#!/usr/bin/env python
"""G-CONF: differential conformance for matplotlib__matplotlib-22871.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). The bundle models ONE behavior: the level-selection +
offset-display decision loop inside `ConciseDateFormatter.format_ticks`
(`implementation_tickOffset`, mapping.md / refinement.md). Over the per-tick
calendar breakdowns it picks the label `level` and decides `show_offset`.

The soundness-critical decision the patch changes is `show_offset`: pre-patch
sets it `False` whenever the varying component is year/month (`level < 2`);
post-patch additionally requires `np.any(unique == 1)` — the value `1` must occur
in that component.

ORACLE: a verbatim re-execution of the REAL post-patch decision loop, using the
genuine `numpy` of the patched testbed (`np.unique`, `len`, `np.any(unique==1)`
over `tickdate[:, level]`). This is exactly the arithmetic `format_ticks` runs.

SHADOW: the op-for-op transliteration of `implementation_tickOffset`
(Solution.lean impl region) — the deep models `column.dedup.length` /
`1 in column` over each column, in pure Python.

Both are fed the SAME fuzzed `tickdate` arrays. Exit 0 iff zero disagreements
over a discrete edge matrix + >=1e5 fuzzed draws. Fuzzing is stdlib-only
(pinned seed 22871); numpy is used ONLY inside the oracle, mirroring the repo.
"""
import json
import random
import sys

SEED = 22871
N_RANDOM = 120_000  # >= 1e5
LEVELS = [5, 4, 3, 2, 1, 0]


# ---- SHADOW of implementation_tickOffset -----------------------------------
# Mirrors Solution.lean impl region exactly (refinement.md):
#   level = 5; show_offset = s0
#   for lvl in [5,4,3,2,1,0]:
#     column = [row[lvl] for row in td]
#     if len(set(column)) > 1:        # 1 < column.dedup.length
#       level = lvl
#       if lvl < 2 and 1 in column:   # decide(lvl<2) && column.contains 1
#         show_offset = False
#       return (level, show_offset)
#     elif lvl == 0:
#       level = 5
#   return (level, show_offset)
def shadow_offset(td, s0):
    level = 5
    show_offset = s0
    for lvl in LEVELS:
        column = [row[lvl] for row in td]
        if len(set(column)) > 1:               # dedup.length > 1
            level = lvl
            if lvl < 2 and (1 in column):       # contains 1
                show_offset = False
            return (level, show_offset)
        elif lvl == 0:
            level = 5
    return (level, show_offset)


# ---- ORACLE: the REAL post-patch decision loop (numpy, as in dates.py) -----
def oracle_offset(td, s0):
    import numpy as np
    tickdate = np.array(td)
    show_offset = s0
    level = 5
    for lv in range(5, -1, -1):
        unique = np.unique(tickdate[:, lv])
        if len(unique) > 1:
            level = lv
            if lv < 2 and np.any(unique == 1):
                show_offset = False
            break
        elif lv == 0:
            level = 5
    return (level, show_offset)


# ---- PREPATCH shadow (the bug): hide whenever level < 2, no `==1` check -----
# Mirrors Solution_prepatch.lean. Negative control: the differential test must
# distinguish the bug from the fix on at least one drawn configuration.
def prepatch_offset(td, s0):
    level = 5
    show_offset = s0
    for lvl in LEVELS:
        column = [row[lvl] for row in td]
        if len(set(column)) > 1:
            level = lvl
            if lvl < 2:
                show_offset = False
            return (level, show_offset)
        elif lvl == 0:
            level = 5
    return (level, show_offset)


# Plausible per-component ranges (year/month/day/hour/minute/second). Values are
# drawn to FREQUENTLY hit the discriminators: month/year columns that do vs.
# don't contain 1; constant vs. varying columns.
def rand_value(rng, j):
    # j: 0=year,1=month,2=day,3=hour,4=minute,5=second
    if j == 0:
        return rng.choice([1, 1, 1997, 1998, 2000, 2021, 2022])
    if j == 1:  # month: bias toward including/excluding 1 (January)
        return rng.choice([1, 1, 2, 3, 5, 8, 11, 12])
    if j == 2:  # day
        return rng.choice([1, 1, 2, 14, 28, 31])
    if j == 3:  # hour
        return rng.randint(0, 23)
    if j == 4:  # minute
        return rng.randint(0, 59)
    return rng.randint(0, 59)  # second


def rand_tickdate(rng):
    n = rng.randint(1, 6)
    # With some probability, make a coarse column constant to exercise the scan.
    rows = []
    base = [rand_value(rng, j) for j in range(6)]
    for _ in range(n):
        row = []
        for j in range(6):
            if rng.random() < 0.4:
                row.append(base[j])              # tends to keep column constant
            else:
                row.append(rand_value(rng, j))
        rows.append(row)
    return rows


def edge_matrix():
    cases = []
    # F2P: Feb..Aug 1997 monthly, NO January -> month varies, no 1 -> offset kept
    cases.append([[1997, 2, 1, 0, 0, 0], [1997, 3, 1, 0, 0, 0],
                  [1997, 5, 1, 0, 0, 0], [1997, 8, 1, 0, 0, 0]])
    # Jan..Mar 1997 -> month varies, contains 1 -> offset hidden
    cases.append([[1997, 1, 1, 0, 0, 0], [1997, 2, 1, 0, 0, 0],
                  [1997, 3, 1, 0, 0, 0]])
    # All identical -> level 5, offset kept
    cases.append([[1997, 1, 1, 0, 0, 0], [1997, 1, 1, 0, 0, 0]])
    # Single tick
    cases.append([[2021, 6, 14, 3, 30, 0]])
    # Year varies, no 1 -> level 0, offset kept (year already in ticks)
    cases.append([[1997, 6, 1, 0, 0, 0], [2002, 6, 1, 0, 0, 0],
                  [2007, 6, 1, 0, 0, 0]])
    # Year varies and includes year 1 -> level 0, offset hidden
    cases.append([[1, 6, 1, 0, 0, 0], [2002, 6, 1, 0, 0, 0]])
    # Day varies (level 2 >= 2) -> offset always kept
    cases.append([[1997, 6, 2, 0, 0, 0], [1997, 6, 14, 0, 0, 0]])
    # Day varies including 1 -> still kept (level >= 2 short-circuits)
    cases.append([[1997, 6, 1, 0, 0, 0], [1997, 6, 14, 0, 0, 0]])
    # Hour varies -> level 3, offset kept
    cases.append([[1997, 6, 1, 1, 0, 0], [1997, 6, 1, 5, 0, 0]])
    return cases


def main():
    rng = random.Random(SEED)
    disagreements = []
    discriminated = False  # prepatch differs from oracle somewhere (sanity)

    def check(td, s0):
        nonlocal discriminated
        o = oracle_offset(td, s0)
        s = shadow_offset(td, s0)
        if tuple(o) != tuple(s):
            disagreements.append({"td": td, "s0": s0,
                                  "oracle": list(o), "shadow": list(s)})
        if tuple(prepatch_offset(td, s0)) != tuple(o):
            discriminated = True

    for td in edge_matrix():
        for s0 in (True, False):
            check(td, s0)
    for _ in range(N_RANDOM):
        td = rand_tickdate(rng)
        s0 = rng.random() < 0.5
        check(td, s0)

    ok = (not disagreements) and discriminated
    print(json.dumps({
        "status": "pass" if ok else "fail",
        "instance": "matplotlib__matplotlib-22871",
        "seed": SEED,
        "n_random": N_RANDOM,
        "disagreements": disagreements[:5],
        "n_disagreements": len(disagreements),
        "prepatch_discriminated": discriminated,
    }))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
