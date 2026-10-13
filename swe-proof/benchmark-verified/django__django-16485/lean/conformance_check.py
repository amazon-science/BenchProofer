#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-16485.

The bundle models ONE function: `floatformat` (`django/template/defaultfilters.py`),
at the fix point. The patch changes a single branch guard:

    -    if not m and p < 0:        # pre-patch
    +    if not m and p <= 0:       # post-patch
             return mark_safe(formats.number_format("%d" % (int(d)), 0, ...))

i.e. a whole-valued `d` with a NON-POSITIVE requested place count `p` is rendered
as a plain integer; otherwise the general (quantize/round) rendering at `abs(p)`
places is used. (The pre-patch `p < 0` guard sent whole values with `p == 0` into
the general branch, which crashes in `Decimal.quantize(Context(prec=0))` — the
reported bug.)

The general digit builder (defaultfilters.py lines 181-198) is PARTIAL even
post-patch: for a whole ZERO value with enough trailing zeros and a small
positive `p` (e.g. `Decimal("0.000")` with `p = 1`, or `Decimal("0E-10")`), the
computed `prec = abs(p) + units + 1` is <= 0 and `Context(prec=...)` raises
`ValueError`, which propagates to the caller. The Lean model represents that
outcome as `none` (`decimalDigits : DecVal → Int → Option String`), and the
modeled result is `Option String`: `none` ↔ the call raises.

The Lean impl `implementation_floatformat` is the R/I skeleton of that choice:

    if decIsWhole(d) and p <= 0:
        return some(numberFormat(str(decIntPart(d)), 0))       # integer branch
    return (decimalDigits(d, p)).map(λ s => numberFormat(s, abs(p)))  # general

The opaque callees are unchanged sub-computations carried identically in spec
and impl (no consumed axiom): `decIsWhole(d) == (int(d) - d == 0)`,
`decIntPart(d) == int(d)`, `decimalDigits(d, p) ==` some(number) via the digit
builder (lines 181-198) or none when it raises, `numberFormat ==`
`formats.number_format`. In G-CONF we model these callees IDENTICALLY on both
legs (a faithful in-process replica) so the differential isolates exactly the
R/I part the impl owns: the branch SELECTION, the argument composition fed to
each branch, and the propagation of the general branch's failure.

  * ORACLE  — a faithful in-process replica of the POST-PATCH `floatformat` at the
    fix point, written with the literal Python guard `not m and p <= 0` over a
    real `Decimal`; a raise from the digit builder propagates and is observed
    as the `none` outcome.
  * SHADOW  — the Lean impl's branch logic via the type bijection (mapping.md):
    `decIsWhole(d) and p <= 0`, with `decIsWhole`/`decIntPart`/`decimalDigits`/
    `numberFormat` the same in-process callees the oracle uses, and
    `decimalDigits` returning None exactly where the builder raises.

They must agree on the rendered outcome (Some string / None) for EVERY input —
in particular at the discriminating point `d` whole and `p == 0` (oracle takes
the integer branch and returns the integer string; a wrong `p < 0` guard would
diverge there), and on the partial-domain points (whole zero, positive `p`,
trailing zeros) where BOTH legs must yield None.

We do NOT stand up Django settings / the localization machinery (heavy, and the
formatting step is an unchanged opaque callee). `numberFormat` is modeled by a
deterministic stand-in `nf(s, k)` used identically on both legs; the fix is about
WHICH branch runs and WHAT is fed to it, not the internals of `number_format`.

stdlib-only; deterministic built-in fuzzer. Pinned seed: 16485 (also in
mapping.md).
"""
import sys
from decimal import Decimal, ROUND_HALF_UP, Context

SEED = 16485
N = 120_000


# --- opaque callees, modeled identically on both legs ------------------------
def nf(s, k):
    """Stand-in for formats.number_format(s, k, ...) under the call's fixed flag
    config. Deterministic; identical on oracle and shadow. The fix does not touch
    this step, so its internals are irrelevant to the differential — only that
    both legs feed it the same (string, place-count)."""
    return "NF(%s|%d)" % (s, k)


def dec_is_whole(d):
    """decIsWhole(d) == (int(d) - d == 0)  ==  Python `not m`."""
    return (int(d) - d) == 0


def dec_int_part(d):
    """decIntPart(d) == int(d)."""
    return int(d)


def decimal_digits_raw(d, p):
    """The patched digit-string builder (defaultfilters.py lines 181-198), the
    general-branch `number`. PARTIAL: for a whole zero `d` whose trailing zeros
    make `prec = abs(p) + units + 1` <= 0, `Context(prec=...)` RAISES
    ValueError; that failure propagates to the caller."""
    m = int(d) - d
    exp = Decimal(1).scaleb(-abs(p))
    tupl = d.as_tuple()
    units = len(tupl[1])
    units += -tupl[2] if m else tupl[2]
    prec = abs(p) + units + 1
    rounded_d = d.quantize(exp, ROUND_HALF_UP, Context(prec=prec))
    sign, digits, exponent = rounded_d.as_tuple()
    digits = [str(digit) for digit in reversed(digits)]
    while len(digits) <= abs(exponent):
        digits.append("0")
    digits.insert(-exponent, ".")
    if sign and rounded_d:
        digits.append("-")
    return "".join(reversed(digits))


def decimal_digits_opt(d, p):
    """decimalDigits(d, p) : Option String — some(number) when the builder
    produces text, none when it raises (the modeled failure outcome)."""
    try:
        return decimal_digits_raw(d, p)
    except (ValueError, ArithmeticError):
        return None


# --- ORACLE: post-patch floatformat at the fix point (literal Python guard) --
def oracle_floatformat(d, p):
    """Returns ('some', text) or None (== the call raises)."""
    m = int(d) - d
    try:
        if not m and p <= 0:                   # the post-patch guard
            return ("some", nf("%d" % (int(d)), 0))
        return ("some", nf(decimal_digits_raw(d, p), abs(p)))
    except (ValueError, ArithmeticError):
        return None                            # raise propagates == none


# --- SHADOW: the Lean impl's branch logic via the bijection ------------------
def shadow_floatformat(d, p):
    """Mirror of implementation_floatformat: Option String outcome."""
    if dec_is_whole(d) and p <= 0:             # decIsWhole(d) && decide (p ≤ 0)
        return ("some", nf(str(dec_int_part(d)), 0))  # some (numberFormat (toString (decIntPart d)) 0)
    dd = decimal_digits_opt(d, p)              # decimalDigits d p
    if dd is None:                             # Option.map over none
        return None
    return ("some", nf(dd, abs(p)))            # .map (fun s => numberFormat s p.natAbs)


# --- deterministic fuzzer (stdlib LCG; no imports beyond decimal/sys) ---------
class LCG:
    def __init__(self, seed):
        self.s = seed & 0xFFFFFFFFFFFF

    def next(self):
        self.s = (self.s * 0x5DEECE66D + 0xB) & 0xFFFFFFFFFFFF
        return self.s

    def randint(self, lo, hi):
        return lo + self.next() % (hi - lo + 1)

    def choice(self, xs):
        return xs[self.next() % len(xs)]


def gen_decimal(rng):
    """Generate a varied Decimal: whole and non-whole, signed, varied scale."""
    kind = rng.randint(0, 4)
    if kind == 0:                              # exact whole integer
        return Decimal(rng.randint(-10000, 10000))
    if kind == 1:                              # whole value with fractional zeros
        n = rng.randint(-1000, 1000)
        places = rng.randint(0, 6)
        return Decimal(n).scaleb(0).quantize(Decimal(1).scaleb(-places)) if places else Decimal(n)
    if kind == 2:                              # genuine fractional
        whole = rng.randint(-1000, 1000)
        frac = rng.randint(0, 999999)
        return Decimal("%d.%06d" % (whole, frac))
    if kind == 3:                              # tiny magnitude
        return Decimal(rng.randint(1, 99)).scaleb(-rng.randint(1, 22))
    return Decimal("0").scaleb(-rng.randint(0, 4))  # signed/zero variants of 0.00


def main():
    rng = LCG(SEED)
    checked = 0
    disagreements = 0
    # explicit boundary cases first — the F2P fix points, the partial-domain
    # (ValueError-propagating) points, and neighbors.
    boundary = [
        (Decimal("0.00"), 0), (Decimal("-0.00"), 0), (Decimal("0"), 0),
        (Decimal("0.0"), 0), (Decimal("123"), 0), (Decimal("123"), -2),
        (Decimal("123"), 2), (Decimal("34.00000"), 0), (Decimal("34.00000"), 3),
        (Decimal("2.5"), 0), (Decimal("2.5"), 2), (Decimal("-12.0"), 0),
        (Decimal("0.00"), 1), (Decimal("0.00"), -1), (Decimal("1000"), 0),
        # partial-domain points (post-patch raise == none on both legs):
        (Decimal("0.000"), 1), (Decimal("-0.000"), 1), (Decimal("0E-10"), 1),
        (Decimal("0E-10"), 5), (Decimal("0.0000"), 2), (Decimal("0.000"), 2),
    ]
    cases = list(boundary)
    for _ in range(N):
        cases.append((gen_decimal(rng), rng.randint(-20, 20)))

    for d, p in cases:
        try:
            o = oracle_floatformat(d, p)
        except Exception as e:
            o = ("EXC", type(e).__name__)
        try:
            s = shadow_floatformat(d, p)
        except Exception as e:
            s = ("EXC", type(e).__name__)
        checked += 1
        if o != s:
            disagreements += 1
            if disagreements <= 10:
                print("DISAGREE d=%r p=%r oracle=%r shadow=%r" % (d, p, o, s),
                      file=sys.stderr)

    status = "pass" if disagreements == 0 else "fail"
    print("checked=%d disagreements=%d status=%s" % (checked, disagreements, status))
    sys.exit(0 if disagreements == 0 else 1)


if __name__ == "__main__":
    main()
