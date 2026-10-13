#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13128 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures) stripped. The @Pure helper `is_datetime_type` (the
only pure helper the impl region calls) copies over as a plain function. The
model carries only ints/bools — no PSeq shim is needed. There are no
@ContractOnly callees in this bundle.

ORACLE: the REAL patched repo function the model models per mapping.md —
`django.db.models.expressions.CombinedExpression.resolve_expression`. The gate
applies patch.diff to /testbed before this script runs (this script does NOT
apply anything itself); PYTHONPATH=/testbed makes the patched module
importable. No database access is performed.

Type bridge (mapping.md section 2), same realization as axiom_check.py:

  * operand type code -> a Value expression whose resolved output type is that
    code (T_UNKNOWN -> a Value with no declared output field, whose output
    type is unresolvable; the other codes -> a Value carrying the matching
    field instance, with T_OTHER realized as an integer field);
  * is_sub -> the subtraction connector vs the addition connector;
  * is_already_temporal -> start from an already-specialised temporal /
    duration expression instance instead of a plain combined one;
  * result kind code <-> the dispatch decision read off the class of the
    resolution result (which specialised wrapper, if any, was NEWLY created:
    a result of the same class as self is the plain outcome).

Input domain: Requires demands both type codes within the modelled enumeration
[0, 5]; the two booleans are unconstrained. The full domain is the finite grid
2 x 2 x 6 x 6 = 144 tuples; boundary coverage enumerates all of it, and the
fuzz phase draws 100000 further Requires-satisfying tuples uniformly at random
(pinned seed), each independently driven through both shadow and oracle.

>= 1e5 Requires-satisfying inputs: 144 boundary (exhaustive) + 100000 fuzz.
Pinned fuzz seed: 13128.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + Django (the system under test) only.
"""
import json
import random
import sys

SEED = 13128
N_FUZZ = 100_000

# --- minimal Django configuration (no database access is performed) ----------
import django  # noqa: E402
from django.conf import settings  # noqa: E402

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=[],
        DATABASES={},
        USE_TZ=False,
    )
    django.setup()

from django.db.models import (  # noqa: E402
    DateField, DateTimeField, TimeField, DurationField, IntegerField,
)
from django.db.models.expressions import (  # noqa: E402
    Value, CombinedExpression, DurationExpression, TemporalSubtraction,
)

# --- enumeration constants from model.py (pure region) -----------------------

T_UNKNOWN = 0     # no usable output type
T_DATE = 1        # date-only field
T_DATETIME = 2    # date+time field
T_TIME = 3        # time-only field
T_DURATION = 4    # duration field
T_OTHER = 5       # any other concrete field (e.g. an integer field)

K_PLAIN = 0       # the generic combined expression (no temporal specialisation)
K_DURATION = 1    # the duration-arithmetic form
K_TEMPORAL = 2    # the temporal-subtraction form


# --- pure helper from model.py, contracts stripped ----------------------------

def is_datetime_type(t):
    """Whether a type code denotes one of the three date/time field kinds."""
    return t == T_DATE or t == T_DATETIME or t == T_TIME


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def resolve_kind(is_already_temporal, is_sub, t_lhs, t_rhs):
    if not is_already_temporal:
        if (t_lhs == T_DURATION or t_rhs == T_DURATION) and t_lhs != t_rhs:
            return K_DURATION
        if is_sub and is_datetime_type(t_lhs) and t_lhs == t_rhs:
            return K_TEMPORAL
    return K_PLAIN


# --- bridge: type code -> a real operand expression ---------------------------

def operand(type_code):
    """A Value whose resolved output type is the given code.

    T_UNKNOWN -> a Value with no declared output field (its output type is
    unresolvable — exactly the 'no usable output type' the model encodes)."""
    if type_code == T_UNKNOWN:
        return Value(1)
    field = {
        T_DATE: DateField,
        T_DATETIME: DateTimeField,
        T_TIME: TimeField,
        T_DURATION: DurationField,
        T_OTHER: IntegerField,
    }[type_code]()
    return Value(None, output_field=field)


SUB = CombinedExpression.SUB
ADD = CombinedExpression.ADD


def real_kind(is_already_temporal, is_sub, t_lhs, t_rhs):
    """Drive the REAL patched resolution and read off the dispatch decision
    (which specialised wrapper, if any, the resolution NEWLY created)."""
    connector = SUB if is_sub else ADD
    lhs, rhs = operand(t_lhs), operand(t_rhs)
    if is_already_temporal:
        # An already-specialised temporal/duration expression; the temporal
        # form only takes (lhs, rhs), so use it for the subtraction connector
        # and the duration form otherwise.
        if is_sub:
            self_expr = TemporalSubtraction(lhs, rhs)
        else:
            self_expr = DurationExpression(lhs, connector, rhs)
    else:
        self_expr = CombinedExpression(lhs, connector, rhs)
    resolved = self_expr.resolve_expression(query=None)
    # The decision is K_PLAIN exactly when no NEW specialised wrapper was
    # created, i.e. the result's class equals self's class (the plain copy
    # outcome; this covers the already-specialised case too).
    if type(resolved) is type(self_expr):
        return K_PLAIN
    if isinstance(resolved, TemporalSubtraction):
        return K_TEMPORAL
    if isinstance(resolved, DurationExpression):
        return K_DURATION
    return K_PLAIN


def check_one(is_already_temporal, is_sub, t_lhs, t_rhs):
    """Run shadow and oracle on one input tuple; return an error string on
    disagreement, else None."""
    # Requires holds by construction:
    assert T_UNKNOWN <= t_lhs <= T_OTHER and T_UNKNOWN <= t_rhs <= T_OTHER
    shadow = resolve_kind(is_already_temporal, is_sub, t_lhs, t_rhs)
    real = real_kind(is_already_temporal, is_sub, t_lhs, t_rhs)
    if shadow != real:
        return ("DISAGREEMENT\n"
                "  input: is_already_temporal=%r is_sub=%r t_lhs=%d t_rhs=%d\n"
                "  shadow (model impl) kind = %d\n"
                "  real (patched repo)  kind = %d"
                % (is_already_temporal, is_sub, t_lhs, t_rhs, shadow, real))
    return None


TYPE_CODES = (T_UNKNOWN, T_DATE, T_DATETIME, T_TIME, T_DURATION, T_OTHER)
BOOLS = (False, True)


def main():
    checked = 0
    n_boundary = 0

    # Boundary: the FULL finite input domain, exhaustively (144 tuples).
    for is_already_temporal in BOOLS:
        for is_sub in BOOLS:
            for t_lhs in TYPE_CODES:
                for t_rhs in TYPE_CODES:
                    err = check_one(is_already_temporal, is_sub, t_lhs, t_rhs)
                    if err:
                        print(err)
                        return 1
                    checked += 1
                    n_boundary += 1

    # Fuzz: 100000 uniform Requires-satisfying tuples, pinned seed. Each is
    # independently driven through both shadow and oracle (fresh operand
    # expressions per call).
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        err = check_one(rng.random() < 0.5, rng.random() < 0.5,
                        rng.choice(TYPE_CODES), rng.choice(TYPE_CODES))
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched resolution on %d inputs "
          "(%d boundary = exhaustive domain + %d fuzz, seed %d)."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
