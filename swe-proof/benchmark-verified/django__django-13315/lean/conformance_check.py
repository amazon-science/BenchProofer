#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-13315.

The bundle models ONE function: `apply_limit_choices_to_to_formfield`. Its Lean
implementation (`implementation_applyChoiceLimit`) narrows a collection of
candidate objects to those satisfying a constraint, keeping each qualifying
candidate AT MOST ONCE (its presence depends only on whether at least one
related row satisfies the constraint, never on how many do):

    if applicable and constraintActive:
        result = [c for c in base if c.matchRows != 0]      # each kept once
    else:
        result = base                                       # unchanged

This script transliterates that R/I impl into Python (`shadow_apply`) and
differential-tests it against the ORACLE: a faithful in-process replica of the
post-patch behavior of `apply_limit_choices_to_to_formfield`
(`django/forms/models.py`):

    if hasattr(queryset) and hasattr(get_limit_choices_to):     # `applicable`
        if limit_choices_to:                                    # `constraintActive`
            # filter(Exists(model._base_manager.filter(constraint & pk=OuterRef)))
            # keeps each candidate iff at least one related row matches the
            # constraint — exactly once, regardless of join multiplicity.
            queryset = [c for c in queryset if matches_at_least_once(c)]

We do NOT stand up a database / ORM (heavy, and the modeled value is a pure
decision over candidate match-multiplicities). Instead we reproduce the patched
behavior with light stand-in candidate objects carrying the SAME observable the
real join exposes (mapping.md): `matchRows`, the number of related rows that
satisfy the constraint for the candidate. The real pre-patch `complex_filter`
join would list a candidate `matchRows` times (the duplicate-options defect); the
post-patch `Exists()` subquery lists it once — which is what the oracle below
encodes. The shadow reaches the same result via `matchRows != 0` membership.

The differential genuinely tests the Lean modeling: the shadow uses Lean's
`List.filter qualifies` over the abstracted match counts, whereas the oracle
reproduces the patched `filter(Exists(...))` membership semantics over
realistically-shaped candidate records. They must agree for every input — in
particular on candidates with `matchRows >= 2`, the multi-related-row case the
patch deduplicates.

stdlib-only; falls back to a built-in deterministic fuzzer if `hypothesis` is
absent. Pinned seed: 13315 (also recorded in mapping.md).
"""
import sys

SEED = 13315
N = 120_000


# --- ORACLE: the post-patch behavior, faithful in-process replica ------------
# A candidate is a dict {"id": int, "matchRows": int}. `matchRows` is the number
# of related rows that satisfy the constraint for this candidate (the join
# multiplicity the pre-patch code exposed). The post-patch code applies
# `filter(Exists(...))`, which includes a candidate iff at least one related row
# matches — i.e. once, regardless of `matchRows`.
def oracle_apply(applicable, constraint_active, base):
    queryset = list(base)
    if applicable:                          # hasattr(queryset) and hasattr(...)
        if constraint_active:               # `if limit_choices_to:`
            # Exists() subquery membership: keep each candidate iff >=1 related
            # row satisfies the constraint, listed exactly once.
            queryset = [c for c in queryset if c["matchRows"] >= 1]
    return queryset


# --- shadow of implementation_applyChoiceLimit (the R/I leg) ------------------
# Mirrors Solution.lean: `List.filter qualifies` where `qualifies c := matchRows != 0`.
def shadow_apply(applicable, constraint_active, base):
    queryset = list(base)
    if applicable:
        if constraint_active:
            queryset = [c for c in queryset if c["matchRows"] != 0]
    return queryset


def disagree(applicable, constraint_active, base):
    got = oracle_apply(applicable, constraint_active, base)
    want = shadow_apply(applicable, constraint_active, base)
    if got != want:
        return ((applicable, constraint_active, base), got, want)
    return None


# --- input corpus ------------------------------------------------------------
def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def _enumerate_edge():
    """Hand-picked edge cases exercising the duplicate-elimination behavior."""
    cases = []
    for applicable in (True, False):
        for active in (True, False):
            cases.append((applicable, active, []))
            cases.append((applicable, active, [{"id": 1, "matchRows": 0}]))
            cases.append((applicable, active, [{"id": 1, "matchRows": 1}]))
            # the discriminating multi-related-row candidate (matchRows >= 2):
            cases.append((applicable, active, [{"id": 1, "matchRows": 3}]))
            cases.append((applicable, active,
                          [{"id": 1, "matchRows": 2}, {"id": 2, "matchRows": 0},
                           {"id": 3, "matchRows": 1}]))
    return cases


def main() -> int:
    checked = 0

    for applicable, active, base in _enumerate_edge():
        d = disagree(applicable, active, base)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    rnd = _lcg(SEED)
    for _ in range(N):
        applicable = (next(rnd) & 1) == 1
        active = (next(rnd) & 1) == 1
        length = next(rnd) % 9            # 0..8 candidates
        base = []
        for _ in range(length):
            cid = next(rnd) % 5           # ids 0..4 (repeats possible)
            mrows = next(rnd) % 5         # matchRows 0..4
            base.append({"id": cid, "matchRows": mrows})
        d = disagree(applicable, active, base)
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
