#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-14122.

The bundle models ONE function: `SQLCompiler.get_group_by`, which accumulates the
list of grouping columns (`expressions`) for an aggregate query
(`django/db/models/sql/compiler.py`). The modeled value is the PRE-collapse
`expressions` list, a PURE function of the following observables (mapping.md):

    metaOrdering : bool                  (bool(self._meta_ordering) — the ordering
                                          came from the model's Meta.ordering)
    gb           : group-by source       (None | True | list[Col])  i.e.
                                          self.query.group_by
    select       : list[(bool, [Col])]   per entry (expr in ref_sources,
                                          expr.get_group_by_cols())
    orderBy      : list[(bool, [Col])]   per entry (is_ref,
                                          expr.get_group_by_cols())
    having       : list[Col]             self.having.get_group_by_cols()

where Col is a column identity (int).

Post-patch rule (the ORDER BY phase is GATED by `not metaOrdering`):

    if gb is None: return []
    expressions = []
    if gb is not True:                       # gb is an explicit list
        expressions += gb_list
    for (covered, cols) in select:
        if covered: continue
        expressions += cols
    if not metaOrdering:
        for (is_ref, cols) in orderBy:
            if not is_ref:
                expressions += cols
    expressions += having
    return expressions

Standing up the full ORM/compiler stack to drive the real `get_group_by` is heavy
and unnecessary: the modeled value is this pure accumulation over the observables
the real method consumes (the downstream collapse_group_by/dedup pass is
unchanged pre/post patch and operates on the already-built list — see mapping.md,
so it is outside the modeled function). The ORACLE below is a faithful in-process
replica of the EXACT patched control flow; the SHADOW is the op-for-op
transliteration of `implementation_getGroupBy` (refinement.md). They compare as
ordered lists of Col (order is observable — `expressions` is built and consumed in
iteration order, and an extra implicit-ordering column would survive dedup).

The fuzzer deliberately varies `metaOrdering` independently and includes the F2P
shape: metaOrdering=True with a non-empty orderBy contributing columns (which
must NOT appear in the result), and the same shape with metaOrdering=False (which
must include them).

stdlib-only. Pinned seed: 14122 (also in mapping.md).
"""
import random
import sys

SEED = 14122
N = 120_000


# --- ORACLE: faithful in-process replica of the patched method ---------------
# gb is one of: ("none",), ("all",), ("explicit", [Col, ...])
def oracle_get_group_by(meta_ordering, gb, select, order_by, having):
    kind = gb[0]
    if kind == "none":
        return []
    expressions = []
    if kind == "explicit":
        for c in gb[1]:
            expressions.append(c)
    # kind == "all": no explicit seed
    for covered, cols in select:
        if covered:
            continue
        for col in cols:
            expressions.append(col)
    if not meta_ordering:                       # <-- the gold's new guard
        for is_ref, cols in order_by:
            if not is_ref:
                for col in cols:
                    expressions.append(col)
    for col in having:
        expressions.append(col)
    return expressions


# --- SHADOW of implementation_getGroupBy (the R/I leg) -----------------------
# Mirrors Solution.lean op-for-op: match on gb, seed explicit cols, append
# uncovered select cols, gate the orderBy phase on `not meta_ordering`, then
# append having; all in order.
def shadow_get_group_by(meta_ordering, gb, select, order_by, having):
    kind = gb[0]
    expressions = []
    if kind == "none":
        return []
    if kind == "all":
        pass
    elif kind == "explicit":
        for c in gb[1]:
            expressions = expressions + [c]
    for entry in select:
        if entry[0]:
            continue
        for col in entry[1]:
            expressions = expressions + [col]
    if not meta_ordering:
        for entry in order_by:
            if not entry[0]:
                for col in entry[1]:
                    expressions = expressions + [col]
    for col in having:
        expressions = expressions + [col]
    return expressions


def disagree(mo, gb, sel, ob, hv):
    got = oracle_get_group_by(mo, gb, sel, ob, hv)
    want = shadow_get_group_by(mo, gb, sel, ob, hv)
    if got != want:
        return ((mo, gb, sel, ob, hv), got, want)
    return None


def _enumerate_edge():
    cases = []
    sel = [(False, [10, 11]), (True, [12]), (False, [])]
    ob = [(False, [20, 21]), (True, [22])]
    hv = [30]
    for gb in (("none",), ("all",), ("explicit", [1, 2])):
        for mo in (True, False):
            cases.append((mo, gb, [], [], []))                 # all phases empty
            cases.append((mo, gb, sel, ob, hv))                # full mix
            cases.append((mo, gb, [], ob, []))                 # F2P core: only ordering
            cases.append((mo, gb, sel, [], hv))                # no ordering
            cases.append((mo, gb, [], [(False, [99])], []))    # single ordering col
    return cases


def _rand_entries(rng):
    out = []
    for _ in range(rng.randint(0, 4)):
        flag = rng.choice([True, False])
        cols = [rng.randint(0, 9) for _ in range(rng.randint(0, 3))]
        out.append((flag, cols))
    return out


def _rand_gb(rng):
    k = rng.choice(["none", "all", "explicit"])
    if k == "explicit":
        return ("explicit", [rng.randint(0, 9) for _ in range(rng.randint(0, 4))])
    return (k,)


def main() -> int:
    checked = 0
    for mo, gb, sel, ob, hv in _enumerate_edge():
        d = disagree(mo, gb, sel, ob, hv)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        mo = rng.choice([True, False])
        gb = _rand_gb(rng)
        sel = _rand_entries(rng)
        ob = _rand_entries(rng)
        hv = [rng.randint(0, 9) for _ in range(rng.randint(0, 3))]
        d = disagree(mo, gb, sel, ob, hv)
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
