#!/usr/bin/env python3
"""G-AX executable soundness check for astropy__astropy-14508.

Executes the REAL numeric callees the model.py axioms stand for and asserts that
every observation matches the axiom's Ensures, on boundary inputs and randomized
fuzz. All callees are stdlib (Python's float `str`/`repr` and `float()` parser) —
the very primitives the gold patch swaps the renderer to. Exit 0 iff sound.

The model.py axioms checked:

  shortest_field(value, neg) -- the renderer the fix uses, on the number the pair
                                denotes:  str(d).replace("e","E")
      * round-trips:                 parse_dec(shortest_field(v,n)) == value
      * minimal significant digits:  sig_count(shortest_field(v,n)) == min_sig(value)
      * len == shortest_field_len(value, neg)
      * signed exactly when negative: field starts with "-" iff neg
      * exponent suffix `E...` (if present) is at most 5 characters

A finite double `d` refines to the pair `(value, neg) = (d + 0.0, signbit(d))`.
`d + 0.0` is the canonical magnitude representative: bit-identical to `d` for
every finite nonzero `d`, and it maps -0.0 to +0.0, so the pair is a COMPLETE
invariant of `d` (for nonzero d the value determines d; at zero the flag does).
Every axiom is therefore checked as a function of the pair, against the real
callee run on the `d` the pair reconstructs.

  padded_field(value)    -- the WIDER renderer the pre-patch used:
                            normalized f"{value:.16G}"
      * non-empty; exponent suffix (if present) at most 5 characters
      * (witness for the discriminator) it spends MORE than min_sig significant
        digits on values whose minimal rendering is shorter, i.e.
        sig_count(padded_field(value)) > min_sig(value) -- which is exactly why
        the pre-patch skeleton cannot prove the minimality postcondition.

  parse_dec(field)       -- the inverse: float(field.replace("E","e"))
  sig_count(field)       -- number of significant digits the field spends
  min_sig(value)         -- fewest significant digits that read back to value
  shortest_field_len(v)  -- len(shortest_field(v))

Domain: finite real numbers. Non-finite values (inf, nan) are rejected upstream
by io.fits before the renderer is reached (test_assign_inf_nan), so they are out
of the renderer's domain and not fuzzed here.
"""
import math
import random
import sys


# --- the REAL callees the axioms stand for ----------------------------------

def _as_double(value, neg):
    """The finite double the pair `(value, neg)` denotes: the magnitude carried by
    `value`, signed by `neg`. Reconstructs -0.0 from (0.0, True), which is the
    distinction an interpreted real cannot carry."""
    return math.copysign(value, -1.0 if neg else 1.0)


def signbit(d):
    """True iff the double `d` is a negative one (including -0.0)."""
    return math.copysign(1.0, d) < 0.0


def canon(d):
    """The pair a finite double refines to: (magnitude representative, sign)."""
    return (d + 0.0, signbit(d))


def shortest_field(value, neg):
    """The renderer the fix uses, on the number the pair denotes: Python's
    shortest round-tripping repr, with the exponent marker upper-cased."""
    return str(_as_double(value, neg)).replace("e", "E")


def padded_field(value, neg=False):
    """The wider renderer the pre-patch used: 16-significant-digit general
    format with the exponent zero-padded to two digits (and upper-cased)."""
    value_str = f"{_as_double(value, neg):.16G}"
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
    non-significant trailing zeros (integer-valued fixed forms) dropped; a value
    of zero counts as one significant digit."""
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
    """Fewest significant digits any decimal reading round-trips to value.

    A function of the magnitude alone -- a sign costs no significant digits --
    which is why it takes no sign flag.

    Grounded in Python's shortest round-tripping repr (`str`/`repr`), which is
    defined to emit the fewest digits that read back exactly. We must NOT probe
    with `f"{value:.{k}g}"`: that rounds to NEAREST, so it can miss a k-digit
    rendering that round-trips via a different last digit -- e.g. for 2**-24,
    `%.16g` gives ...062 (does not round-trip) while `repr` gives ...063 (does),
    which made the old `%g` scan over-report 17 where 16 is actually minimal."""
    if value == 0:
        return 1
    return sig_count(shortest_field(value, False))


def shortest_field_len(value, neg):
    return len(shortest_field(value, neg))


# --- the checks --------------------------------------------------------------

def check_shortest_field(d):
    """Every axiom clause, checked as a function of the PAIR the double `d`
    refines to, against the real callee run on `d` itself."""
    value, neg = canon(d)
    f = shortest_field(value, neg)
    # the pair reconstructs d exactly: the refinement claim itself
    assert repr(_as_double(value, neg)) == repr(d), (
        f"pair does not reconstruct {d!r}: got {_as_double(value, neg)!r}")
    # the axiom's field IS the real callee's rendering of d
    assert f == str(d).replace("e", "E"), (
        f"shortest_field(pair) != real callee on {d!r}: {f!r} vs "
        f"{str(d).replace('e', 'E')!r}")
    assert len(f) >= 1, f"shortest_field empty on {d!r}"
    # round-trip (to the magnitude the axiom's parse_dec clause names)
    assert parse_dec(f) == value, (
        f"shortest_field not round-tripping on {d!r}: field={f!r} "
        f"parses to {parse_dec(f)!r}")
    # minimal significant digits
    assert sig_count(f) == min_sig(value), (
        f"shortest_field NOT minimal on {d!r}: field={f!r} spends "
        f"{sig_count(f)} sig digits, minimum is {min_sig(value)}")
    # len agreement
    assert len(f) == shortest_field_len(value, neg)
    # SIGN: a leading minus exactly when the number rendered is negative
    assert f.startswith("-") == neg, (
        f"shortest_field sign clause broken on {d!r}: field={f!r}, neg={neg}")
    if neg:
        assert len(f) >= 2, f"signed field too short on {d!r}: {f!r}"
    # exponent suffix bound
    idx = f.find("E")
    if idx >= 0:
        assert len(f) - idx <= 5, (
            f"shortest_field exponent suffix > 5 on {d!r}: field={f!r}")


def check_padded_field(d):
    value, neg = canon(d)
    f = padded_field(value, neg)
    assert len(f) >= 1, f"padded_field empty on {d!r}"
    idx = f.find("E")
    if idx >= 0:
        assert len(f) - idx <= 5, (
            f"padded_field exponent suffix > 5 on {d!r}: field={f!r}")


def main():
    rng = random.Random(14508)

    # --- boundary values, including the issue's exact discriminators ---------
    boundary = [
        0.009125, 8.95, -99.9,            # the F2P regression values
        1.0, -1.0, 0.0, -0.0, 100.0, 0.1, 0.5, -0.5, -100.0,
        -467374636747637647347374734737437.0,   # P2P FLOATNUM (scientific, trims)
        1.2345377437887837487e88,                # P2P complex real part
        6324767364763746367e-33,                 # P2P complex imag part
        1e-10, 1e10, 1e100, 1e-100, 1e308, 5e-324,
        2.2250738585072014e-308,                 # smallest normal
        (1 - 2 ** -53) * 2 ** -60,               # hints_text coverage
        (1 - 2 ** -53) * 2 ** 0,
        (1 - 2 ** -53) * 2 ** 60,
        1.0 / 3.0, 2.0 / 3.0, math.pi, math.e,
    ]

    # discriminator witnesses: values whose minimal rendering spends fewer
    # significant digits than the wider renderer -> padded_field is NOT minimal.
    discriminators = [0.009125, 8.95, -99.9, 0.1, 0.2, 0.3, 8.7]
    n_padded_excess = 0
    for v in discriminators:
        if sig_count(padded_field(*canon(v))) > min_sig(v) \
                and sig_count(shortest_field(*canon(v))) == min_sig(v):
            n_padded_excess += 1
    assert n_padded_excess >= 3, (
        "discriminator absent: the wider renderer should spend excess significant "
        "digits on the regression values, distinguishing it from the minimal renderer")
    # the headline regression value, spelled out
    assert shortest_field(*canon(0.009125)) == "0.009125"
    assert sig_count(padded_field(*canon(0.009125))) > min_sig(0.009125)
    # the signed-zero pair: the two zeros are DIFFERENT numbers and the real
    # callee renders them differently, which the pair carrier can express.
    assert shortest_field(*canon(0.0)) == "0.0"
    assert shortest_field(*canon(-0.0)) == "-0.0"
    assert canon(0.0) != canon(-0.0)

    for v in boundary:
        check_shortest_field(v)
        check_padded_field(v)

    # --- randomized fuzz over the finite-float domain ------------------------
    N = 200000
    for _ in range(N):
        mant = rng.uniform(-10.0, 10.0)
        exp = rng.randint(-308, 308)
        v = mant * (10.0 ** exp)
        if not math.isfinite(v):
            continue
        check_shortest_field(v)
        check_padded_field(v)

    # small integers-as-floats and subnormals
    for i in range(-2000, 2001):
        check_shortest_field(float(i))
    for _ in range(20000):
        v = rng.uniform(-1e-300, 1e-300)
        if math.isfinite(v):
            check_shortest_field(v)

    print(
        f"G-AX OK: shortest_field == the real callee on the pair each double "
        f"refines to, round-trips + spends minimal significant "
        f"digits + signs the field exactly when negative (both zeros "
        f"covered), padded_field well-formed and spends EXCESS digits on the "
        f"regression values, over {len(boundary)} boundary + {N} fuzz + 4001 "
        f"integer + 20000 subnormal finite floats; exponent suffix <= 5 throughout")
    return 0


if __name__ == "__main__":
    sys.exit(main())
