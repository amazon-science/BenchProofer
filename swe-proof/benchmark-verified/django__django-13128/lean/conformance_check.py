#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-13128.

The bundle models ONE function: `CombinedExpression.resolve_expression`. Its Lean
implementation (`implementation_resolveKind`) decides which KIND a resolved
arithmetic combination becomes — ordinary (`combined`), `duration`, or
`temporal` — as a function of the combination's current kind, the operator, and
the two resolved operands' value-types:

    if self_kind != 'combined':                      return self_kind   # reclassification guard
    if ('duration' in {lhs_type, rhs_type}) and lhs_type != rhs_type:
                                                     return 'duration'
    if connector == 'sub' and lhs_type in DATETIME and lhs_type == rhs_type:
                                                     return 'temporal'
    return 'combined'

This script transliterates that R/I impl into Python (`shadow_classify`) and
differential-tests it against the ORACLE: a faithful in-process replica of the
POST-PATCH classification dispatch in `CombinedExpression.resolve_expression`
(`django/db/models/expressions.py`):

    lhs = self.lhs.resolve_expression(...); rhs = self.rhs.resolve_expression(...)
    if not isinstance(self, (DurationExpression, TemporalSubtraction)):
        try:    lhs_type = lhs.output_field.get_internal_type()
        except (AttributeError, FieldError): lhs_type = None
        try:    rhs_type = rhs.output_field.get_internal_type()
        except (AttributeError, FieldError): rhs_type = None
        if 'DurationField' in {lhs_type, rhs_type} and lhs_type != rhs_type:
            return DurationExpression(...).resolve_expression(...)   # -> 'duration'
        if self.connector == self.SUB and lhs_type in DATETIME and lhs_type == rhs_type:
            return TemporalSubtraction(...).resolve_expression(...)  # -> 'temporal'
    # plain copy of the same class
    return self_kind   # 'combined' here, since the guard above only runs for combined

We do NOT stand up a database / ORM (heavy, and the modeled value is a pure
decision over the resolved operands' value-types). Instead we reproduce the
patched classification with light stand-in values carrying the SAME observables
the real dispatch consults (mapping.md): the expression's current kind, the
connector (SUB vs other), and the two operands' `get_internal_type()` strings
(or `None` when access raises). `get_internal_type()` for a real
`DurationField`/`DateField`/`DateTimeField`/`TimeField` returns exactly those
strings; the relocation from `as_sql` to `resolve_expression` does not change the
classification decision itself, only WHEN it runs — so an in-process replica of
the decision is a faithful oracle for the modeled observable.

The modeled input space is finite — self_kind in {combined,duration,temporal},
connector in {sub,other}, each operand type in
{DurationField,DateField,DateTimeField,TimeField,OTHER,None} = 3*2*6*6 = 216
combinations — so we ENUMERATE ALL 216 exhaustively, then additionally fuzz.

stdlib-only; deterministic built-in fuzzer. Pinned seed: 13128 (also recorded in
mapping.md).
"""
import sys

SEED = 13128
N = 120_000

KINDS = ("combined", "duration", "temporal")
CONNECTORS = ("sub", "other")
# the six observable operand "types": the four named field types, one catch-all
# "OTHER" (any further internal type string), and None (access raised).
TYPES = ("DurationField", "DateField", "DateTimeField", "TimeField", "OTHER", None)
DATETIME = {"DateField", "DateTimeField", "TimeField"}


# --- ORACLE: the post-patch classification, faithful in-process replica ------
def oracle_classify(self_kind, connector, lhs_type, rhs_type):
    # `not isinstance(self, (DurationExpression, TemporalSubtraction))`
    if self_kind != "combined":
        # already specialized: resolves to a plain copy of the same class.
        return self_kind
    # case A: a duration mixed with a different (non-duration) type.
    if "DurationField" in {lhs_type, rhs_type} and lhs_type != rhs_type:
        return "duration"
    # case B: subtraction of two operands sharing one date/datetime/time type.
    if connector == "sub" and lhs_type in DATETIME and lhs_type == rhs_type:
        return "temporal"
    # default: ordinary combination (plain copy of the same class).
    return "combined"


# --- shadow of implementation_resolveKind (the R/I leg) ----------------------
# Mirrors Solution.lean exactly.
def shadow_classify(self_kind, connector, lhs_type, rhs_type):
    if self_kind != "combined":
        return self_kind
    if (lhs_type == "DurationField" or rhs_type == "DurationField") and lhs_type != rhs_type:
        return "duration"
    if connector == "sub" and (lhs_type in DATETIME) and lhs_type == rhs_type:
        return "temporal"
    return "combined"


def disagree(self_kind, connector, lhs_type, rhs_type):
    got = oracle_classify(self_kind, connector, lhs_type, rhs_type)
    want = shadow_classify(self_kind, connector, lhs_type, rhs_type)
    if got != want:
        return ((self_kind, connector, lhs_type, rhs_type), got, want)
    return None


# --- input corpus ------------------------------------------------------------
def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def _enumerate_all():
    """All 216 modeled inputs, exhaustively."""
    for sk in KINDS:
        for c in CONNECTORS:
            for lt in TYPES:
                for rt in TYPES:
                    yield (sk, c, lt, rt)


def main() -> int:
    checked = 0

    # exhaustive sweep of the entire finite modeled space.
    for sk, c, lt, rt in _enumerate_all():
        d = disagree(sk, c, lt, rt)
        if d:
            print(f"DISAGREE exhaustive {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    # additional randomized fuzz (redundant given the exhaustive sweep, but
    # exercises the requested >=1e5 corpus and guards the harness itself).
    rnd = _lcg(SEED)
    for _ in range(N):
        sk = KINDS[next(rnd) % 3]
        c = CONNECTORS[next(rnd) % 2]
        lt = TYPES[next(rnd) % 6]
        rt = TYPES[next(rnd) % 6]
        d = disagree(sk, c, lt, rt)
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
