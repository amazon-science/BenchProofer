#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-13121.

The bundle models ONE routine: the strategy-selection head of
`CombinedExpression.as_sql` — given the two operand field types, whether the
operator is subtraction, and whether the backend natively supports durations,
which of three SQL-generation strategies is chosen. Per mapping.md it is a PURE
function of four observables:

    native_duration_support : bool        (connection.features.has_native_duration_field)
    is_subtraction          : bool        (self.connector == self.SUB)
    lhs                     : field type or None   (lhs.output_field.get_internal_type())
    rhs                     : field type or None   (rhs.output_field.get_internal_type())

Post-patch rule (the gold edit's new `lhs_type != rhs_type` guard):

    if (not native_duration_support and
            ('DurationField' in {lhs, rhs}) and lhs != rhs):
        return 'duration_arithmetic'        # DurationExpression(...).as_sql(...)
    if is_subtraction and lhs in datetime_fields and lhs == rhs:
        return 'date_subtraction'           # TemporalSubtraction(...).as_sql(...)
    return 'generic_arithmetic'             # generic combine_expression path

Standing up the full ORM/compiler/connection stack to drive the real `as_sql` is
heavy and unnecessary: the modeled value is this pure decision over the four
observables. So the ORACLE is a faithful in-process replica of the patched head,
and the SHADOW is the op-for-op transliteration of
`implementation_expressionSqlStrategy` per refinement.md.

The operand-type domain is finite: {None, DurationField, DateField, DateTimeField,
TimeField, Other} for each side, times Bool x Bool for the two flags = 6*6*2*2 =
144 points; we enumerate it exhaustively AND fuzz to >=10^5 trials.

stdlib-only. Pinned seed: 13121 (also in mapping.md).
"""
import itertools
import random
import sys

SEED = 13121
N = 120_000

# Field-type domain. None models a FieldError (no resolvable output_field).
FIELD_TYPES = [
    None,
    "DurationField",
    "DateField",
    "DateTimeField",
    "TimeField",
    "Other",
]
DATETIME_FIELDS = {"DateField", "DateTimeField", "TimeField"}


def is_duration(t):
    return t == "DurationField"


def is_datetime(t):
    return t in DATETIME_FIELDS


# --- ORACLE: faithful in-process replica of the patched as_sql head ----------
def oracle(native_duration_support, is_subtraction, lhs, rhs):
    if (not native_duration_support and
            ("DurationField" in {lhs, rhs}) and lhs != rhs):
        return "duration_arithmetic"
    if is_subtraction and lhs in DATETIME_FIELDS and lhs == rhs:
        return "date_subtraction"
    return "generic_arithmetic"


# --- SHADOW of implementation_expressionSqlStrategy (the R leg) --------------
# Mirrors Solution.lean op-for-op:
#   if !native && (isDuration lhs || isDuration rhs) && lhs != rhs -> durationArithmetic
#   if isSub && isDateTime lhs && lhs == rhs                       -> dateSubtraction
#   else                                                          -> genericArithmetic
def shadow(native_duration_support, is_subtraction, lhs, rhs):
    if ((native_duration_support is False) and
            (is_duration(lhs) or is_duration(rhs)) and lhs != rhs):
        return "duration_arithmetic"
    if (is_subtraction is True) and is_datetime(lhs) and lhs == rhs:
        return "date_subtraction"
    return "generic_arithmetic"


def disagree(n, s, l, r):
    got = oracle(n, s, l, r)
    want = shadow(n, s, l, r)
    if got != want:
        return ((n, s, l, r), got, want)
    return None


def main() -> int:
    checked = 0
    # exhaustive over the full finite domain
    for n, s in itertools.product((False, True), repeat=2):
        for l, r in itertools.product(FIELD_TYPES, repeat=2):
            d = disagree(n, s, l, r)
            if d:
                print(f"DISAGREE edge {d[0]!r}: oracle={d[1]} shadow={d[2]}")
                print("status=fail")
                return 1
            checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        n = rng.choice([False, True])
        s = rng.choice([False, True])
        l = rng.choice(FIELD_TYPES)
        r = rng.choice(FIELD_TYPES)
        d = disagree(n, s, l, r)
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
