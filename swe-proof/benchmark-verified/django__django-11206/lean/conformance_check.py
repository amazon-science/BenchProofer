#!/usr/bin/env python3
r"""G-CONF for django__django-11206.

The gold patch is already applied to /testbed when this runs. We compare the
R/I Python shadow of `implementation_formatNumber` (the Lean impl, transliterated
op-for-op per refinement.md) against the REAL patched
`django.utils.numberformat.format`, over >=1e5 fuzzed Decimal inputs. Zero
disagreements => exit 0.

Model (refinement.md):
  result = renderDecimal(snapValue(number, decimal_pos), …)
where
  * snapValue(number, decimal_pos):
      - decimal_pos is None            -> number unchanged
      - decimal_pos = d, |number| < 10^(-max(d,1))  -> Decimal('0')
      - otherwise                      -> number unchanged
    The cutoff 10^(-max(d,1)) is the MODEL's `cutoffOf` (computed here
    independently of the patch's `Decimal('0.'+'1'.rjust(...))` string formula,
    so a wrong cutoff is caught).
  * renderDecimal = the UNCHANGED value-to-string rendering tail of `format`
    (everything from `_, digits, exponent = number.as_tuple()` onward). It is the
    A-reference: we recover it by stripping the inserted guard from the REAL
    patched source and exec'ing the result as the base-commit `format`. Applying
    the base-commit `format` to an ALREADY-snapped value IS exactly
    `renderDecimal(snapped, …)` (the base function has no snap).

  * Oracle = the REAL patched `format`(number, …).
  * Shadow = base_format(snapValue(number, decimal_pos), …).

This is non-circular: if `snapValue` (incl. its cutoff) diverges from the real
patch's snap on any input, oracle and shadow disagree.

Type bijection (mapping.md): number:ℚ <-> Decimal (exact value);
decimalPos:Option Nat <-> decimal_pos (None / non-negative int);
grouping:Int <-> grouping (single int); result:String <-> returned str.
stdlib-only; no hypothesis required.
"""
import os
import random
import re
import sys
import types
from decimal import Decimal, getcontext, localcontext

# Exact, generous precision for the magnitude comparison (powers of ten only).
getcontext().prec = 80

# --- configure Django settings before importing the formatter ----------------
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=False,
        USE_TZ=False,
        USE_L10N=False,
        USE_THOUSAND_SEPARATOR=False,
        DATABASES={},
        INSTALLED_APPS=[],
        USE_I18N=False,
    )
    django.setup()

from django.utils import numberformat as real_nf
patched_format = real_nf.format


def build_base_format():
    """Recover the base-commit (unpatched) `format` = the A-reference renderer.

    Strip the inserted guard block (everything the patch added between the
    `if isinstance(number, Decimal):` header and the `# Format values with more
    than 200 digits` comment) from the REAL patched source, then exec it.
    """
    src_path = real_nf.__file__
    if src_path.endswith(".pyc"):
        src_path = src_path[:-1]
    with open(src_path, "r") as fh:
        src = fh.read()
    base_src, n = re.subn(
        r"(if isinstance\(number, Decimal\):\n)"
        r".*?"
        r"(\n        # Format values with more than 200 digits)",
        r"\1\2",
        src,
        flags=re.DOTALL,
    )
    if n != 1:
        raise SystemExit("G-CONF ERROR: could not locate/strip the inserted guard "
                         "(patch shape changed); n=%d" % n)
    if "too small to affect" in base_src:
        raise SystemExit("G-CONF ERROR: guard not fully stripped from base source")
    mod = types.ModuleType("numberformat_base")
    mod.__dict__["__file__"] = src_path
    exec(compile(base_src, src_path + " (base)", "exec"), mod.__dict__)
    return mod.format


base_format = build_base_format()


def model_cutoff(d):
    """MODEL `cutoffOf d = 1 / 10^(max d 1)` (independent of the patch formula)."""
    return Decimal(1) / (Decimal(10) ** max(d, 1))


def snap_value(number, decimal_pos):
    """R transliteration of snapValue (Lean): precision-gated magnitude-to-zero."""
    if decimal_pos is None:
        return number
    if abs(number) < model_cutoff(decimal_pos):
        return Decimal(0)
    return number


def shadow(number, decimal_sep, decimal_pos, grouping, thousand_sep,
           force_grouping, use_l10n):
    """renderDecimal(snapValue(number, decimal_pos), …) — snap, then unchanged tail."""
    snapped = snap_value(number, decimal_pos)
    return base_format(snapped, decimal_sep, decimal_pos, grouping,
                       thousand_sep, force_grouping, use_l10n)


def oracle(number, decimal_sep, decimal_pos, grouping, thousand_sep,
           force_grouping, use_l10n):
    return patched_format(number, decimal_sep, decimal_pos, grouping,
                          thousand_sep, force_grouping, use_l10n)


# --- input pool ---------------------------------------------------------------
def rand_decimal_string(rng):
    """A decimal string that exercises tiny magnitudes straddling cutoffs,
    ordinary values, negatives, zero, and very large magnitudes."""
    kind = rng.random()
    sign = "-" if rng.random() < 0.5 else ""
    if kind < 0.45:
        # tiny magnitude near a cutoff boundary: m * 10^-e
        e = rng.randint(1, 320)
        mant = rng.choice(["1", "9", "1234", "5", "10", "99", "100", "2"])
        return "%s%se-%d" % (sign, mant, e)
    if kind < 0.65:
        # value exactly at / just under a power-of-ten cutoff
        e = rng.randint(0, 12)
        return "%s1e-%d" % (sign, e)
    if kind < 0.85:
        # ordinary mid-range decimal
        whole = rng.randint(0, 99999)
        frac = rng.randint(0, 999999)
        return "%s%d.%06d" % (sign, whole, frac)
    # very large magnitude (scientific-notation path; snap never fires)
    e = rng.randint(15, 9999)
    return "%s9e%d" % (sign, e)


def rand_decimal_pos(rng):
    r = rng.random()
    if r < 0.20:
        return None
    return rng.choice([0, 0, 1, 2, 2, 3, 3, 8, 8, 10, 20, 50])


# F2P fixtures + neighbours (mapping.md / test_numberformat.py).
FIXED = [
    ("1e-200", 2), ("1e-199", 2), ("1e-201", 2),
    ("9e-19", 2), (".00000000000099", 0),
    ("0." + "0" * 299 + "1234", 3),          # ~1.234e-300 -> '0.000'
    ("0.00000001", 8), ("1e-7", 8), ("1e-8", 8), ("1e-9", 8),
    ("1e-10", 8), ("1e-11", 8),
    ("1" + "0" * 300, 3),
    ("1234", 2), ("1234.2", None), ("1234", None), ("-1234.33", 1),
    ("0", 2), ("0", 0), ("0", None), ("0.001", 3), ("0.0009", 3),
    ("0.1", 0), ("0.09", 0), ("0.05", 1), ("0.04", 1),
    ("3.", None), ("3.0", None), ("1.23", None),
    ("9e9999", None), ("9e201", None), ("1.2345e999", 2), ("9e-999", None),
]


def main():
    rng = random.Random(11206)  # pinned seed (mapping.md)
    N = 100_000
    disagreements = 0
    first = None

    def one_case(value, decimal_pos, idx):
        nonlocal disagreements, first
        decimal_sep = rng.choice([".", ",", "·"])
        grouping = rng.choice([0, 0, 3, 2])
        thousand_sep = rng.choice(["", ",", " ", "."])
        force_grouping = rng.random() < 0.3
        use_l10n = rng.choice([None, True, False])
        try:
            number = Decimal(value)
        except Exception:
            return
        try:
            o = oracle(number, decimal_sep, decimal_pos, grouping,
                       thousand_sep, force_grouping, use_l10n)
        except Exception as e:
            o = ("RAISE", type(e).__name__)
        try:
            s = shadow(number, decimal_sep, decimal_pos, grouping,
                       thousand_sep, force_grouping, use_l10n)
        except Exception as e:
            s = ("RAISE", type(e).__name__)
        if o != s:
            disagreements += 1
            if first is None:
                first = (value, decimal_pos, decimal_sep, grouping,
                         thousand_sep, force_grouping, use_l10n, o, s)

    i = 0
    for value, dp in FIXED:
        one_case(value, dp, i)
        i += 1
    while i < N:
        one_case(rand_decimal_string(rng), rand_decimal_pos(rng), i)
        i += 1

    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements; first=%r" % (disagreements, N, first))
        return 1
    print("G-CONF OK: %d inputs, 0 disagreements" % N)
    return 0


if __name__ == "__main__":
    sys.exit(main())
