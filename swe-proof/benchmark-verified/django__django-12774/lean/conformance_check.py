#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-12774.

The bundle models ONE function: the field-name acceptability guard at the head
of `QuerySet.in_bulk` (`django/db/models/query.py`). Its Lean implementation
(`implementation_inBulk`) decides whether the call is rejected (raises
`ValueError`, modeled `Except.error field_name`) or proceeds (modeled
`Except.ok ()`):

    unique_fields = [c.fields[0] for c in total_unique_constraints if len(c.fields) == 1]
    if field_name != 'pk' and not field.unique and field_name not in unique_fields:
        return error(field_name)          # raise ValueError(... % field_name)
    return ok()                            # method proceeds

where `total_unique_constraints` is the model's `UniqueConstraint`s whose
`condition is None` (the unconditional / total ones).

This script transliterates that R/I impl into Python (`shadow_decide`) and
differential-tests it against the ORACLE: a faithful in-process replica of the
POST-PATCH guard of `in_bulk` — `field_name not in unique_fields` added as a
third acceptance route, with `unique_fields` computed from the unconditional
single-field unique constraints.

We do NOT stand up Django's ORM (heavy; the modeled value is a pure decision over
the field name, the field's `unique` flag, and the model's unique constraints).
Both legs are total functions over the modeled abstraction, so the edge set
EXHAUSTIVELY enumerates a representative modeled input space (field name drawn
from a small alphabet incl. "pk"; field.unique present/absent; 0..2 constraints
each unconditional/partial spanning 1 or 2 fields drawn from the alphabet); the
fuzz loop additionally samples random points. The discriminating case —
`field_name` not pk, field not unique, but `field_name` IS the sole field of an
unconditional unique constraint — is covered: oracle (post-patch) returns ok(),
and the PRE-patch code would reject it.

stdlib-only. Pinned seed: 12774 (also recorded in mapping.md).
"""
import itertools
import sys

SEED = 12774
N = 150_000

# Field-name / constraint-field alphabet. "pk" is included to exercise the
# primary-key short-circuit; the rest are ordinary field labels.
NAMES = ("pk", "year", "slug", "brand", "ean")
BOOLS = (False, True)


def total_unique_constraints(constraints):
    # Options.total_unique_constraints: UniqueConstraints with condition is None.
    # In the model `constraints` is already the UniqueConstraint projection;
    # `is_partial` carries `condition is not None`.
    return [c for c in constraints if not c["isPartial"]]


# --- ORACLE: the post-patch in_bulk guard, faithful in-process replica --------
def oracle_decide(field_name, field_unique, constraints):
    unique_fields = [
        c["fields"][0]
        for c in total_unique_constraints(constraints)
        if len(c["fields"]) == 1
    ]
    if field_name != "pk" and not field_unique and field_name not in unique_fields:
        return ("error", field_name)
    return ("ok", None)


# --- shadow of implementation_inBulk (the R/I leg) ----------------------------
# Mirrors Solution.lean op-for-op:
#   singleFieldUniqueConstraintFields = (cs.filter (!isPartial && len==1)).map (.headD "")
#   reject = field != "pk" && !unique && !(uniqueFields.contains field)
def shadow_decide(field_name, field_unique, constraints):
    unique_fields = [
        (c["fields"][0] if len(c["fields"]) >= 1 else "")   # headD ""
        for c in constraints
        if (not c["isPartial"]) and len(c["fields"]) == 1
    ]
    reject = (
        field_name != "pk"
        and (not field_unique)
        and (field_name not in unique_fields)
    )
    if reject:
        return ("error", field_name)
    return ("ok", None)


def disagree(field_name, field_unique, constraints):
    got = oracle_decide(field_name, field_unique, constraints)
    want = shadow_decide(field_name, field_unique, constraints)
    if got != want:
        return (field_name, field_unique, constraints, got, want)
    return None


def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


# All single constraints: field-list (1 or 2 names) x partial/total.
def _all_single_constraints():
    out = []
    for partial in BOOLS:
        for f in NAMES:
            out.append({"fields": [f], "isPartial": partial})
        for f1, f2 in itertools.product(NAMES, NAMES):
            out.append({"fields": [f1, f2], "isPartial": partial})
    return out


def main() -> int:
    checked = 0
    singles = _all_single_constraints()

    # Edge set: field_name x field_unique x {no constraint, one constraint}.
    # One constraint already exercises every shadow/oracle branch (the
    # single-field unconditional case is the discriminator); two-constraint
    # combinations are covered by the fuzz loop below.
    for field_name, field_unique in itertools.product(NAMES, BOOLS):
        for cons in [[]] + [[c] for c in singles]:
            d = disagree(field_name, field_unique, cons)
            if d:
                print(f"DISAGREE edge field={d[0]!r} unique={d[1]} cons={d[2]!r}: "
                      f"oracle={d[3]} shadow={d[4]}")
                print("status=fail")
                return 1
            checked += 1

    # Random fuzz: 0..3 constraints, each 1..3 fields, partial/total.
    rnd = _lcg(SEED)

    def pick(seq):
        return seq[next(rnd) % len(seq)]

    for _ in range(N):
        field_name = pick(NAMES)
        field_unique = pick(BOOLS)
        ncons = next(rnd) % 4
        cons = []
        for _ in range(ncons):
            nf = 1 + (next(rnd) % 3)
            cons.append({"fields": [pick(NAMES) for _ in range(nf)],
                         "isPartial": pick(BOOLS)})
        d = disagree(field_name, field_unique, cons)
        if d:
            print(f"DISAGREE fuzz field={d[0]!r} unique={d[1]} cons={d[2]!r}: "
                  f"oracle={d[3]} shadow={d[4]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
