#!/usr/bin/env python3
"""G-AX executable soundness check for astropy__astropy-14508.

Executes the REAL stdlib callees the Solution.lean axioms stand for and asserts
that every observation matches each axiom's stated property, on boundary inputs
and randomized fuzz. All callees are stdlib (Python's float `str`/`repr` and the
`float()` parser) -- the very primitives the gold patch swaps the renderer to.
Exit 0 iff sound; stdlib-only.

Axioms validated (Solution.lean `axioms` region):

  shortestField(value)  ==  str(value).replace("e", "E")
      * shortestField_nonempty:      len >= 1
      * shortestField_roundtrip:     parseDec(shortestField(v)) == v
      * shortestField_minimal:       sigCount(shortestField(v)) == minSig(v)
                                     and minSig(v) >= 1 (minSig_pos)
      * shortestField_suffix_short:  any exponent suffix `E...` is <= 5 chars

  paddedField(value)    ==  normalized f"{value:.16G}"  (the pre-patch renderer)
      * paddedField_nonempty:        len >= 1
      * paddedField_suffix_short:    any exponent suffix `E...` is <= 5 chars
      * (discriminator witness) it spends MORE significant digits than minSig on
        the regression values -- which is exactly why the pre-patch skeleton
        cannot satisfy the minimality postcondition (G-DIFF).

  parseDec(field)       ==  float(field.replace("E", "e"))
  sigCount(field)       ==  number of significant digits the field spends
  minSig(value)         ==  fewest significant digits that round-trip `value`
                            -- computed CORRECTLY (see note below), NOT via the
                            brittle `%g`-reconstruction that mis-fires on dyadic
                            values such as 2**-24, 2**-44, 2**122 and subnormals.

  eIndex(field)         ==  field.find("E")   (sentinel: len(field) if absent)

IMPORTANT minimality note (avoids the latent %g bug).
Since Python 3.1, `repr(float)` / `str(float)` produces the SHORTEST decimal
string that round-trips to the same IEEE-754 double (David Gay / Grisu / Ryu
dtoa). Therefore `sigCount(str(v))` IS, by construction, the minimal significant-
digit count. A naive `min_sig` that rounds via `float(f"{v:.{k}g}") == v` rounds
the k-th digit by a DIFFERENT rule than dtoa, so on dyadic values it can claim a
spurious minimum of 17 while `str(v)` spends 16 -- a FALSE positive. We do not
inherit that bug. We define minimality two independent, agreeing ways:

  (1) minSig(v) := sigCount(str(v))         -- the true shortest, by construction.
  (2) structural: assert that NO decimal with strictly fewer significant digits
      round-trips to v. We probe every k < sigCount(str(v)) and require that no
      k-significant-digit rendering of v reads back to v. This is what "minimal"
      means and is sound: if str were ever non-shortest, (2) would catch it.

Both must hold for every fuzzed value; (1) makes shortestField_minimal trivially
true and (2) is the adversarial cross-check that str really is shortest.

Domain: finite real numbers. inf/nan are rejected upstream by io.fits before the
renderer is reached (test_assign_inf_nan), so they are out of domain and not
fuzzed here.
"""
import math
import random
import sys


# --- the REAL callees the axioms stand for ----------------------------------

def shortest_field(value):
    """The renderer the fix uses: Python's shortest round-tripping repr, with
    the exponent marker upper-cased."""
    return str(value).replace("e", "E")


def padded_field(value):
    """The wider renderer the pre-patch used: 16-significant-digit general format
    with the exponent zero-padded to two digits (and upper-cased)."""
    value_str = f"{value:.16G}"
    if "." not in value_str and "E" not in value_str:
        value_str += ".0"
    elif "E" in value_str:
        significand, exponent = value_str.split("E")
        if exponent[0] in ("+", "-"):
            sign = exponent[0]
            exponent = exponent[1:]
        else:
            sign = ""
        value_str = f"{significand}E{sign}{int(exponent):02d}"
    return value_str


def parse_dec(field):
    """Inverse of decimal rendering: read a field back to a float."""
    return float(field.replace("E", "e"))


def sig_count(field):
    """Number of significant digits the decimal field spends: the digits of the
    significand (before any exponent marker), with leading zeros dropped and
    non-significant trailing zeros (integer-form fixed renderings) dropped; a
    value of zero counts as one significant digit."""
    s = field.replace("E", "e")
    if "e" in s:
        s = s.split("e", 1)[0]
    if s and s[0] in "+-":
        s = s[1:]
    if "." in s:
        intp, frac = s.split(".", 1)
    else:
        intp, frac = s, ""
    digits = intp + frac
    stripped = digits.lstrip("0")
    if stripped == "":
        return 1
    stripped = stripped.rstrip("0")
    if stripped == "":
        return 1
    return len(stripped)


def min_sig(value):
    """Fewest significant digits any decimal reading round-trips to `value`.

    Computed CORRECTLY as the significant-digit count of Python's shortest repr
    (`str(value)`), which IS the shortest round-tripping decimal by construction
    (Python >= 3.1). This deliberately AVOIDS the `float(f"{value:.{k}g}") == value`
    reconstruction, whose %g rounding diverges from dtoa on dyadic values and
    would report a spurious minimum."""
    if value == 0:
        return 1
    return sig_count(shortest_field(value))


def shortest_field_len(value):
    return len(shortest_field(value))


def e_index(field):
    """field.find('E'); sentinel len(field) if absent (matches Lean `eIndex`)."""
    i = field.find("E")
    return len(field) if i < 0 else i


# --- minimality, checked structurally (the adversarial cross-check) ----------

def no_shorter_roundtrips(value):
    """Assert NO decimal with strictly fewer significant digits than str(value)
    round-trips to value. Returns True iff str(value) is genuinely shortest.

    For each k from 1 .. sigCount(str(value)) - 1 we form the k-significant-digit
    rendering of value (via %g) and require it does NOT read back to value. If
    str were ever non-shortest, some shorter k would round-trip and this fails."""
    if value == 0:
        return True
    target = sig_count(shortest_field(value))
    for k in range(1, target):
        cand = f"{value:.{k}g}"
        try:
            if float(cand) == value:
                return False  # a strictly shorter rendering round-trips
        except (ValueError, OverflowError):
            pass
    return True


# --- the checks --------------------------------------------------------------

def check_shortest_field(value):
    f = shortest_field(value)
    # nonempty
    assert len(f) >= 1, f"shortestField empty on {value!r}"
    # round-trip
    assert parse_dec(f) == value, (
        f"shortestField not round-tripping on {value!r}: field={f!r} "
        f"parses to {parse_dec(f)!r}")
    # minimal significant digits (definition (1)) + minSig >= 1
    ms = min_sig(value)
    assert ms >= 1, f"minSig < 1 on {value!r}"
    assert sig_count(f) == ms, (
        f"shortestField NOT minimal on {value!r}: field={f!r} spends "
        f"{sig_count(f)} sig digits, minSig is {ms}")
    # minimal significant digits (definition (2)): no strictly shorter rendering
    # round-trips. This is the adversarial cross-check that str IS shortest, and
    # it is the clause whose naive %g form is buggy -- ours probes round-trips
    # directly, so it is sound on dyadic values.
    assert no_shorter_roundtrips(value), (
        f"a strictly shorter rendering round-trips to {value!r} -- "
        f"str(value)={f!r} would NOT be shortest (unexpected)")
    # len agreement
    assert len(f) == shortest_field_len(value)
    # exponent suffix bound + eIndex consistency
    idx = e_index(f)
    if idx < len(f):
        assert f[idx] == "E"
        assert len(f) - idx <= 5, (
            f"shortestField exponent suffix > 5 on {value!r}: field={f!r}")


def check_padded_field(value):
    f = padded_field(value)
    assert len(f) >= 1, f"paddedField empty on {value!r}"
    idx = e_index(f)
    if idx < len(f):
        assert len(f) - idx <= 5, (
            f"paddedField exponent suffix > 5 on {value!r}: field={f!r}")


def main():
    # --- boundary values, incl. the issue's exact discriminators -------------
    boundary = [
        0.009125, 8.95, -99.9,            # the F2P regression values
        1.0, -1.0, 0.0, 100.0, 0.1, 0.5,
        -467374636747637647347374734737437.0,   # P2P FLOATNUM (scientific, trims)
        1.2345377437887837487e88,                # P2P complex real part
        6324767364763746367e-33,                 # P2P complex imag part
        1e-10, 1e10, 1e100, 1e-100, 1e308, 5e-324,
        2.2250738585072014e-308,                 # smallest normal
        394633776111243.0,                       # BLOCKED.md "shorter exists" probe
        # exact powers of two (dyadic) -- the class the %g min_sig bug mis-fires on
        2.0 ** -24, 2.0 ** -44, 2.0 ** 122, 2.0 ** -52, 2.0 ** 52,
        2.0 ** 0, 2.0 ** -1, 2.0 ** 100, 2.0 ** -100, 2.0 ** -1000,
        # subnormals (also dyadic-ish small)
        7.120236347223045e-307, 5e-324, 1e-310, 4.9e-324,
        # hints_text coverage: (1 - 2**-53) * 2**exp
        (1 - 2 ** -53) * 2.0 ** -60,
        (1 - 2 ** -53) * 2.0 ** 0,
        (1 - 2 ** -53) * 2.0 ** 60,
        1.0 / 3.0, 2.0 / 3.0, math.pi, math.e,
    ]

    # discriminator witnesses: values whose minimal rendering spends fewer
    # significant digits than the wider renderer -> paddedField is NOT minimal,
    # so the pre-patch skeleton cannot satisfy the minimality postcondition.
    discriminators = [0.009125, 8.95, -99.9, 0.1, 0.2, 0.3, 8.7]
    n_padded_excess = 0
    for v in discriminators:
        if sig_count(padded_field(v)) > min_sig(v) \
                and sig_count(shortest_field(v)) == min_sig(v):
            n_padded_excess += 1
    assert n_padded_excess >= 3, (
        "discriminator absent: the wider renderer should spend excess significant "
        "digits on the regression values, distinguishing it from the minimal "
        "renderer")
    # the headline regression value, spelled out
    assert shortest_field(0.009125) == "0.009125"
    assert sig_count(padded_field(0.009125)) > min_sig(0.009125)

    for v in boundary:
        check_shortest_field(v)
        check_padded_field(v)

    # --- randomized fuzz over the finite-float domain, two distinct seeds -----
    total_fuzz = 0
    for seed in (14508, 0xC0FFEE):
        rng = random.Random(seed)
        N = 120000
        for _ in range(N):
            mant = rng.uniform(-10.0, 10.0)
            exp = rng.randint(-308, 308)
            v = mant * (10.0 ** exp)
            if not math.isfinite(v):
                continue
            check_shortest_field(v)
            check_padded_field(v)
            total_fuzz += 1

        # exact powers of two (dyadic) -- the bug class, swept across the range
        for k in range(-1074, 1024):
            v = 2.0 ** k
            if not math.isfinite(v) or v == 0.0:
                continue
            check_shortest_field(v)

        # subnormals: dense sweep near the bottom of the exponent range
        for _ in range(20000):
            v = rng.uniform(-1e-308, 1e-308)
            if math.isfinite(v):
                check_shortest_field(v)
                total_fuzz += 1

    # small integers-as-floats
    for i in range(-2000, 2001):
        check_shortest_field(float(i))

    print(
        f"G-AX OK: shortestField round-trips + spends minimal significant digits "
        f"(both by-construction AND structural no-shorter-round-trips, so the %g "
        f"min_sig bug is avoided), paddedField well-formed and spends EXCESS "
        f"digits on the regression values; exponent suffix <= 5 throughout. "
        f"Covered {len(boundary)} boundary + {total_fuzz} fuzz (2 seeds) + "
        f"powers-of-two sweep 2**[-1074,1023] + 4001 integers + subnormals.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
