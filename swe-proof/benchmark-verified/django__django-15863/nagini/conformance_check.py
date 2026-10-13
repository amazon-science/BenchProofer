#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15863 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert) stripped — `reconstruct_digits`, the
verified backward copy loop over the significant-digit list. The @Pure helpers
(`significand_budget`, `narrowed_from`, `narrowed_to_significand`) copy over
as plain functions on a small immutable-tuple PSeq shim; they are spec-side
and serve here only as an internal sanity cross-check. There are no
@ContractOnly callees in this bundle.

ORACLE: the REAL patched repo function the model models per mapping.md —
`django.template.defaultfilters.floatformat`. The gate applies patch.diff to
/testbed before this script runs. `reconstruct_digits` models the
value-reconstruction step inside `floatformat` (input value -> the exact
Decimal `d` the rest of the filter formats). The digit sequence of that
reconstructed `d` is observable through the filter's output: formatting a
Decimal at exactly its own fractional scale with the unlocalized arg suffix
("<frac>u") makes the downstream quantize a no-op, so the printed number
carries `d`'s significant digits verbatim (leading positional zeros are not
significant and Decimal parsing of the output discards them; trailing
fractional zeros are significant and survive). Parsing the output back with
`decimal.Decimal` recovers `d.as_tuple().digits`.

TYPE BRIDGE (mapping.md section 2): a value <-> the List[int] of its exact
significant decimal digits, `Decimal.as_tuple().digits`. Sign and exponent are
positional metadata outside the carrier; generation therefore fixes the
observation to the value's own scale and compares digit tuples only. The
Requires asks only for a readable digit list, so every finite Decimal's digit
tuple is a Requires-satisfying input; generation covers the value population
that maps onto it (arbitrary precision, both signs, integral and fractional
scales, zeros with scale).

>= 1e5 Requires-satisfying inputs: boundary cases + a precision-threshold
sweep around the binary-significand budget + 100000 fuzz values.
Pinned fuzz seed: 215863.

Exit 0 iff zero disagreements; on disagreement prints the input and both
digit sequences and exits 1. stdlib only.
"""
import json
import random
import sys
from decimal import Decimal

SEED = 215863
N_FUZZ = 100000


# --- PSeq shim: immutable sequence with the operations the pure region uses --

class PSeq(object):
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __hash__(self):
        return hash(self._t)


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- pure helpers from model.py, contracts stripped ---------------------------

def significand_budget():
    return 17


def narrowed_from(s, budget):
    if len(s) == 0:
        return PSeq(0).take(0)
    if budget > 0:
        return PSeq(s[0]) + narrowed_from(s.drop(1), budget - 1)
    return PSeq(0) + narrowed_from(s.drop(1), 0)


def narrowed_to_significand(s):
    return narrowed_from(s, significand_budget())


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def reconstruct_digits(text):
    result = []  # type: list
    i = len(text)
    while i > 0:
        c = text[i - 1]
        # (the stripped Assert lines carried only proof-side sequence facts)
        result = [c] + result
        i = i - 1
    return result


# --- oracle: observe the reconstructed value's digits via the real filter -----

def real_digits(floatformat, value):
    """Digit tuple of the Decimal the REAL patched `floatformat` reconstructs
    from `value`, observed by formatting at the value's own fractional scale,
    unlocalized (no grouping, '.' separator), and parsing the output back.
    Returns a list of ints, or an error string if the output is unparsable."""
    exponent = value.as_tuple().exponent
    frac = -exponent if exponent < 0 else 0
    out = floatformat(value, "%du" % frac)
    try:
        parsed = Decimal(str(out))
    except Exception as exc:  # noqa: BLE001 - report, don't crash the diff
        return "unparsable filter output %r (%s)" % (str(out), exc)
    return list(parsed.as_tuple().digits)


def check(floatformat, value):
    """Run shadow and oracle on one value; return an error string on
    disagreement, else None."""
    digits = list(value.as_tuple().digits)   # bridge: value -> List[int]
    shadow = reconstruct_digits(digits)
    real = real_digits(floatformat, value)
    if isinstance(real, str):
        return "ORACLE ERROR on %r: %s" % (value, real)
    if shadow != real:
        return ("DISAGREEMENT on value %r (digit carrier %r):\n"
                "  shadow (impl region)  = %r\n"
                "  real (patched filter) = %r"
                % (value, digits, shadow, real))
    return None


def boundary_values():
    return [
        Decimal("0"),
        Decimal("0.00"),
        Decimal("-0.00"),
        Decimal("9"),
        Decimal("09.000"),
        Decimal("340"),
        Decimal("555.555"),
        Decimal("0.12345"),
        Decimal("1.42"),
        Decimal("-1.42"),
        Decimal("0.001"),
        Decimal("-0.001"),
        Decimal("1.100"),
        Decimal("1E-7"),
        Decimal("1.5E-21"),
        Decimal("0.0000000000000000000015"),
        # around and beyond the binary-significand budget
        Decimal("1.2345678901234567"),        # 17 significant digits
        Decimal("1.23456789012345678"),       # 18 significant digits
        Decimal("42.12345678901234567890"),
        Decimal("123456.123456789012345678901"),
        Decimal("-123456.123456789012345678901"),
        Decimal("-123456789012345678901234567890"),
        Decimal("100000000000000000000000"),
        Decimal("0." + "0" * 30 + "1"),
        Decimal("1." + "9" * 40),
    ]


def fuzz_value(rng):
    ndig = rng.randint(1, 40)
    first = rng.choice("123456789")
    rest = "".join(rng.choice("0123456789") for _ in range(ndig - 1))
    digs = first + rest
    shape = rng.random()
    if shape < 0.15:
        # small magnitude: leading positional zeros before the digits
        text = "0." + "0" * rng.randint(0, 8) + digs
    elif shape < 0.25:
        # integral (scale 0), possibly with trailing zero digits
        text = digs + "0" * rng.randint(0, 4)
    else:
        point = rng.randint(1, ndig)
        text = digs[:point] + "." + digs[point:] if point < ndig else digs
    if rng.random() < 0.5:
        text = "-" + text
    if rng.random() < 0.02:
        text = rng.choice(["0", "0.0", "0.000", "-0.00"])
    return Decimal(text)


def main():
    # Configure minimal settings, then import the real patched filter.
    from django.conf import settings
    settings.configure(USE_I18N=False, USE_THOUSAND_SEPARATOR=False)
    from django.template.defaultfilters import floatformat

    checked = 0

    # internal sanity cross-check of the copied pure region (spec-side only):
    # the shadow is the identity, and the lossy pure model differs from it
    # exactly on inputs longer than the budget.
    long_digits = list(range(10)) * 3
    assert reconstruct_digits(long_digits) == long_digits
    assert ToSeq(list(narrowed_to_significand(ToSeq(long_digits)))) != ToSeq(long_digits)
    short_digits = [1, 2, 3]
    assert list(narrowed_to_significand(ToSeq(short_digits))) == short_digits

    boundary = boundary_values()
    for v in boundary:
        err = check(floatformat, v)
        if err:
            print(err)
            return 1
        checked += 1

    # precision-threshold sweep: every length from 1 to 40 significant digits,
    # crossing the binary-significand budget, several digit patterns each
    sweep = 0
    for k in range(1, 41):
        pats = [
            "1" + "".join(str((i * 7 + 1) % 10) for i in range(k - 1)),
            "9" * k,
            "1" + "0" * (k - 1),
        ]
        for digs in pats:
            digs = digs[:k]
            for text in (digs,
                         digs[:1] + "." + digs[1:] if k > 1 else digs + ".0",
                         "0.00" + digs,
                         "-" + digs[:1] + "." + digs[1:] if k > 1 else "-" + digs):
                err = check(floatformat, Decimal(text))
                if err:
                    print(err)
                    return 1
                checked += 1
                sweep += 1

    # randomized fuzz over precision, scale, and sign (pinned seed)
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        err = check(floatformat, fuzz_value(rng))
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched filter's reconstructed digit "
          "sequence on %d inputs (%d boundary + %d sweep + %d fuzz, seed %d); "
          "0 disagreements." % (checked, len(boundary), sweep, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
