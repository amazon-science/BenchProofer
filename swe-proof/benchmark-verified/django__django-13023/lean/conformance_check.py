#!/usr/bin/env python3
"""G-CONF — django__django-13023.

Mechanical cross-language differential test of the R/I shadow of
`implementation_toPython` (Solution.lean) against the faithfully reconstructed
POST-PATCH `DecimalField.to_python`, over >=1e5 fuzzed inputs.

Model under test (Solution.lean impl region), in terms of the input
classification (mapping.md bijection):

    if v.isNone        -> returned
    elif v.isFloat     -> returned
    else (run decimal.Decimal(value)):
        none  (returns a Decimal)            -> returned
        some e (raises a low-level error)    -> validationError   # ALL kinds

Reference = the real post-patch method body, run directly:

    if value is None: return value                       # returned
    if isinstance(value, float): create_decimal_from_float(value)   # returned
    try: decimal.Decimal(value)                          # returned
    except (InvalidOperation, TypeError, ValueError): ValidationError

stdlib-only. exit 0 iff zero disagreements over all fuzzed inputs.
"""
import decimal
import itertools
import sys

SEED = 13023  # pinned (mapping.md)

# ----------------------------------------------------------------------------
# Reference: the faithful POST-PATCH to_python, reduced to its observable
# outcome ("returned" | "validationError" | "propagated").  This mirrors
# patch.diff exactly (the widened except tuple).
# ----------------------------------------------------------------------------
RETURNED = "returned"
VALIDATION_ERROR = "validationError"
PROPAGATED = "propagated"

CTX = decimal.Context(prec=4)  # like DecimalField(max_digits=4).context


def reference_outcome(value):
    """Observable outcome of the real post-patch DecimalField.to_python."""
    if value is None:
        return RETURNED
    if isinstance(value, float):
        # self.context.create_decimal_from_float(value): inf/nan do not raise.
        try:
            CTX.create_decimal_from_float(value)
            return RETURNED
        except Exception:  # pragma: no cover - float branch never raises here
            return PROPAGATED
    try:
        decimal.Decimal(value)
        return RETURNED
    except (decimal.InvalidOperation, TypeError, ValueError):
        return VALIDATION_ERROR
    except Exception:  # any other escaping low-level failure
        return PROPAGATED


# ----------------------------------------------------------------------------
# Shadow: classify a Python value into the Lean `Value` fields, then run the
# Solution.lean impl branch logic on that classification.
# ----------------------------------------------------------------------------
def classify_conv(value):
    """Return None if decimal.Decimal(value) succeeds, else a tag string for
    the low-level failure kind.  Also returns whether the failure was OUTSIDE
    the modeled taxonomy (an escaping exception), which the model does not
    cover and which must be flagged as a disagreement."""
    try:
        decimal.Decimal(value)
        return (None, False)
    except decimal.InvalidOperation:
        return ("notANumber", False)
    except TypeError:
        return ("unsupportedType", False)
    except ValueError:
        return ("malformedValue", False)
    except Exception:
        return ("__escaping__", True)


def shadow_outcome(value):
    """The Solution.lean impl, evaluated on the classification of `value`."""
    if value is None:
        return RETURNED, False
    if isinstance(value, float):
        return RETURNED, False
    conv, escaping = classify_conv(value)
    if escaping:
        # The model has no branch for an escaping low-level failure; surface it
        # so the differential test fails rather than silently masking it.
        return PROPAGATED, True
    if conv is None:
        return RETURNED, False
    return VALIDATION_ERROR, False  # some e -> validationError, ALL kinds


# ----------------------------------------------------------------------------
# Fuzz corpus: cover every branch + the patch's failure modes densely.
# ----------------------------------------------------------------------------
def corpus():
    # Deterministic LCG (no Math.random equivalent needed; reproducible).
    state = SEED & 0xFFFFFFFF

    def rnd(n):
        nonlocal state
        state = (1103515245 * state + 12345) & 0x7FFFFFFF
        return state % n

    # 1) explicit boundary / FAIL_TO_PASS-style values
    boundary = [
        None, (), [], {}, set(), object(), complex(), complex(1, 2),
        "non-numeric string", b"non-numeric byte-string", b"",
        "abc", "", "   ", "nan", "inf", "-inf", "Infinity", "NaN",
        "1", "1.0", "-1.5", "1e10", "  2.5  ", "0", "00", "+3",
        "1_000", "1,000", "0x10", "1/2", "٤", "1.2.3",
        0, 1, -1, 999999, True, False,
        0.0, -0.0, 2.0625, 2.1875, 1.5, float("inf"), float("-inf"),
        float("nan"), 1e308, 1e-308,
        bytearray(b"12"), bytearray(b"xx"),
        decimal.Decimal("1.5"), decimal.Decimal("NaN"),
        [1, 2], {"a": 1}, {1, 2}, (1, 2),
    ]

    for v in boundary:
        yield v

    # 2) random strings (mix of numeric-ish and junk) -> Decimal / Invalid
    digits = "0123456789+-.eE_,/xnaifNAIF "
    for _ in range(60000):
        n = rnd(8)
        s = "".join(digits[rnd(len(digits))] for _ in range(n))
        yield s

    # 3) random ints / floats (returned, or float branch)
    for _ in range(20000):
        yield rnd(2_000_000) - 1_000_000
    for _ in range(20000):
        whole = rnd(1_000_000) - 500_000
        frac = rnd(1_000_000)
        yield whole + frac / 1_000_000.0

    # 4) random bytes / bytearrays (TypeError) + structural containers
    for _ in range(15000):
        n = rnd(6)
        b = bytes(rnd(256) for _ in range(n))
        yield b
    structural = [(), [], {}, set(), object(), complex(rnd(5), rnd(5))]
    for combo in itertools.islice(itertools.cycle(structural), 5000):
        yield combo


def main():
    total = 0
    disagreements = 0
    first_fail = None
    for value in corpus():
        total += 1
        ref = reference_outcome(value)
        shadow, escaping = shadow_outcome(value)
        if escaping:
            # Model taxonomy was not exhaustive for this value.
            disagreements += 1
            if first_fail is None:
                first_fail = ("escaping-low-level-failure", repr(value)[:80], ref)
            continue
        if ref != shadow:
            disagreements += 1
            if first_fail is None:
                first_fail = (repr(value)[:80], ref, shadow)

    if disagreements:
        print("status=fail")
        print("total=%d disagreements=%d" % (total, disagreements))
        print("first_fail=%r" % (first_fail,))
        return 1

    print("status=pass")
    print("total=%d disagreements=0" % total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
