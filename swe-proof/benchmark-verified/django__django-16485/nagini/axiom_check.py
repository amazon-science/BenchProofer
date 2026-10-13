#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-16485.

REQUIRES THE GOLD PATCH APPLIED (apply_gold=True). This script asserts
POST-PATCH facts about the real filter (e.g. `floatformat("0.00", 0) == "0"`,
`floatformat("5.0", 0) == "5"`); on the bare base image (pre-patch) the
A-reference is the fixed behaviour, so `floatformat("0.00", 0)` still RAISES and
this check returns rc=1. The G-AX harness MUST apply the gold patch before
invoking this script. This is correct for an A-reference: the deep model is
validated against the real (post-fix) callee that the gold patch produces.

There is no consumed @ContractOnly axiom in model.py: the changed behaviour is
modelled DEEPLY (the pure `rendered` branch-selection over the digit folds
`int_render` / `zeros_seq`). This script validates that deep model as an
A-REFERENCE against the REAL Django display filter under test, and validates
the unchanged localisation callee `formats.number_format` as digit-content
preserving on the early-return integer string.

The deep model `rendered(int_value, frac_zero, p)`:

  * BARE-INTEGER regime — value is exactly integral (no fractional remainder,
    `frac_zero`) AND a non-positive number of decimal places `p <= 0`: the core
    rendering is the bare integer `int_render(int_value)` (digits, leading '-'
    for negatives) and contains NO decimal separator '.'.

  * SEPARATOR-BEARING regime — every other case (non-integral value, or `p > 0`):
    the CORE rendering (the digit string the filter builds before handing it to
    the localisation callee) contains a decimal separator '.'.

Soundness is checked at two layers:

  1. END-TO-END (real callee): the REAL `floatformat` over boundary + fuzz
     inputs returns exactly `int_render(int_value)` in the bare-integer regime
     (the localisation callee preserves that integer string — the F2P
     observable).  The fix is localised to this regime: in the separator-
     bearing regime the REAL post-patch filter agrees with the pre-patch
     filter (no behavioural change there).

  2. CORE model (the precise digit string the patch's branch produces): a
     faithful replica of the post-patch `floatformat` core — the deterministic
     `decimal`-stdlib computation the patch leaves unchanged — exhibits the
     separator-presence discriminator the model encodes: '.' present exactly
     when NOT (integral and p <= 0).

  3. A-reference `formats.number_format`: preserves the digit content of the
     bare integer string (decimal_pos=0, no grouping).

Discriminator: the PRE-PATCH guard (`p < 0`) sends an integral value at p == 0
into the precision-computing branch, which for "0.00" raises
`ValueError: valid range for prec is [1, MAX_PREC]` and for other integral
values emits a degenerate trailing-separator core string — exactly what
`model_prepatch.py` predicts and the frozen postcondition forbids.

Imports are stdlib + Django (the repo under test); exit 0 iff sound.
"""
import sys
from decimal import Decimal, ROUND_HALF_UP, Context

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        USE_I18N=False,
        USE_TZ=False,
        INSTALLED_APPS=[],
        DATABASES={},
    )
django.setup()

from django.template.defaultfilters import floatformat  # noqa: E402
from django.utils import formats  # noqa: E402


# --- deep-model reference encodings (kept in lock-step with model.py) --------

def int_render(int_value):
    """model.py `int_render`: bare integer rendering as a character string —
    digits with a leading '-' for negatives, NO decimal separator."""
    return str(int(int_value))


def is_integral(value):
    """model.py `frac_zero`: True iff the Decimal value has no fractional
    remainder (m == int(d) - d == 0), matching the real filter's `not m`."""
    d = Decimal(str(value))
    return (int(d) - d) == 0


def floatformat_core(value, p, guard_le):
    """Faithful replica of the `floatformat` CORE digit-string construction
    (the value handed to the localisation callee). `guard_le` selects the
    post-patch guard `p <= 0` (True) or the pre-patch guard `p < 0` (False).
    Mirrors model.py `rendered` at the core layer."""
    d = Decimal(str(value))
    m = int(d) - d
    if not m and (p <= 0 if guard_le else p < 0):
        return "%d" % int(d)                      # bare-integer regime
    exp = Decimal(1).scaleb(-abs(p))
    tupl = d.as_tuple()
    units = len(tupl[1])
    units += -tupl[2] if m else tupl[2]
    prec = abs(p) + units + 1
    rounded_d = d.quantize(exp, ROUND_HALF_UP, Context(prec=prec))  # may raise
    sign, digits, exponent = rounded_d.as_tuple()
    digits = [str(digit) for digit in reversed(digits)]
    while len(digits) <= abs(exponent):
        digits.append("0")
    digits.insert(-exponent, ".")
    if sign and rounded_d:
        digits.append("-")
    return "".join(reversed(digits))              # separator-bearing core


# --- the checks --------------------------------------------------------------

def check_bare_integer_end_to_end(value, p):
    """Integral value, p <= 0: the REAL filter returns exactly the deep model
    bare integer rendering, with no decimal separator (F2P observable)."""
    observed = floatformat(value, p)
    expected = int_render(Decimal(str(value)))
    assert observed == expected, (
        "deep model unsound (bare-integer regime) for floatformat(%r, %r): "
        "real filter gave %r, deep model int_render gives %r"
        % (value, p, observed, expected))
    assert "." not in observed, (
        "bare-integer regime must have no decimal separator: %r" % observed)


def check_separator_core(value, p):
    """Non-integral value or p > 0: the CORE digit string the filter builds
    contains a decimal separator '.' (separator-bearing regime)."""
    core = floatformat_core(value, p, guard_le=True)
    assert "." in core, (
        "separator-bearing regime must have a '.' in the core string for "
        "(%r, %r): core=%r" % (value, p, core))


def check_fix_localised(value, p):
    """In the separator-bearing regime the REAL post-patch filter agrees with
    the pre-patch filter — the fix changes nothing outside the bare-integer
    regime."""
    post = floatformat(value, p)
    if post in ("inf", "-inf", "nan"):
        return
    pre = formats.number_format(
        floatformat_core(value, p, guard_le=False), abs(p),
        use_l10n=False, force_grouping=False)
    assert post == pre, (
        "fix not localised: post-patch %r != pre-patch %r for (%r, %r)"
        % (post, pre, value, p))


def check_number_format_reference():
    """A-reference: `formats.number_format` lays out the bare integer string
    preserving its digit content (decimal_pos=0, no grouping)."""
    for n in [0, 1, 5, 10, 100, -3, -10, 12345, -98765, 2 ** 40]:
        s = "%d" % n
        out = formats.number_format(s, 0, use_l10n=False, force_grouping=False)
        assert out == s, (
            "number_format altered digit content of %r -> %r" % (s, out))
        assert "." not in out, "number_format introduced a separator: %r" % out


def main():
    # Integral values (frac_zero True): all must satisfy is_integral.
    integral_values = [
        "0.00", "0.0", "0", "1.00", "5.0", "-0.00", "-3.00", "10.00",
        "100", "-100.000", "42", "-42", "999.0", "1000000.00",
        Decimal("0.00"), Decimal("1.00"), Decimal("-7.0"), Decimal("0"),
        0, 1, -1, 7, -7, 123, -123,
    ]
    for v in integral_values:
        assert is_integral(v), "test setup: %r should be integral" % (v,)

    # --- bare-integer regime end-to-end (real callee) --------------------
    bare_checks = 0
    for v in integral_values:
        for p in [0, -1, -2, -5]:
            check_bare_integer_end_to_end(v, p)
            bare_checks += 1

    # --- separator-bearing regime: core discriminator + fix localisation --
    sep_checks = 0
    for v in integral_values:
        for p in [1, 2, 6]:                 # integral but p > 0
            check_separator_core(v, p)
            check_fix_localised(v, p)
            sep_checks += 1
    nonintegral = ["0.5", "1.25", "-0.499", "3.14159", "0.001", "-2.5",
                   Decimal("0.5"), Decimal("-1.5"),
                   "0.000000000000000000015"]
    for v in nonintegral:
        for p in [0, -1, 1, 2, 20]:         # non-integral (any p)
            check_separator_core(v, p)
            check_fix_localised(v, p)
            sep_checks += 1

    # --- A-reference: number_format preserves integer digit content -------
    check_number_format_reference()

    # --- specific F2P / P2P observables -----------------------------------
    assert floatformat("0.00", 0) == "0", floatformat("0.00", 0)
    assert floatformat(Decimal("0.00"), 0) == "0", floatformat(Decimal("0.00"), 0)
    assert floatformat(0, 6) == "0.000000", floatformat(0, 6)
    assert floatformat(-0.499, 0) == "0", floatformat(-0.499, 0)
    assert floatformat("5.0", 0) == "5", floatformat("5.0", 0)

    # --- discriminator: PRE-PATCH guard p < 0 diverges on integral & p==0 --
    crashed = False
    try:
        floatformat_core("0.00", 0, guard_le=False)   # pre-patch core
    except Exception as e:  # ValueError: valid range for prec is [1, MAX_PREC]
        crashed = True
        assert "prec" in str(e), "unexpected pre-patch error: %r" % (e,)
    assert crashed, ("discriminator failed: pre-patch guard should crash on "
                     "floatformat('0.00', 0)")
    pre5 = floatformat_core("5.0", 0, guard_le=False)
    assert pre5 != "5" and "." in pre5, (
        "discriminator failed: pre-patch core should be separator-bearing for "
        "5.0 at p=0, got %r" % pre5)
    assert floatformat_core("5.0", 0, guard_le=True) == "5"

    print("G-AX OK: deep model `rendered` validated against real floatformat: "
          "%d bare-integer end-to-end (== int_render) + %d separator-bearing "
          "core observations; number_format A-reference digit-content "
          "preserving; fix localised to the bare-integer regime; pre-patch "
          "(p<0) crashes on '0.00' and diverges on '5.0', both forbidden by "
          "the frozen postcondition." % (bare_checks, sep_checks))
    return 0


if __name__ == "__main__":
    sys.exit(main())
