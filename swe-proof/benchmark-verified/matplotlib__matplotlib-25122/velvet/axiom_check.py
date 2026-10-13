#!/usr/bin/env python3
"""G-AX executable soundness check for matplotlib__matplotlib-25122.

Executes the REAL callee (`numpy.ndarray.sum`, i.e. the patched `window.sum()`
reduction) on boundary windows and randomized fuzzing, and asserts that every
observation satisfies the deep model's postcondition `WithinRoundoff` (the
`pure` region of Solution.lean, transliterated below).

The single kind-A check:

  (A-reference) the real `numpy` reduction `window.sum()` satisfies the deep
      model's guarantee: its result lies within `roundoff_bound` of the exact
      order-preserving SIGNED total `list_sum`:
        |np.sum(window) - list_sum(coeffs)| <= n * 2**-52 * sum(|coeffs|)

WHY A TOLERANCE AND NOT AN EQUALITY (audit correction, G-PANEL-2). An earlier
revision of this file asserted `list_sum == float(window.sum())` EXACTLY, and
mapping.md claimed that drawing coefficients from exactly-float-representable
rationals made `np.sum` bit-exact against the exact rational total. That claim
is FALSE, and this script is where the falsehood was laundered: element-wise
exact representability does NOT make the REDUCTION exact, because the
accumulator rounds at every step. The old fuzz domain (dyadic numerators in
[-1024, 1024], denominators <= 2**6, length <= 32) was simply too small to
expose it. Counterexamples that were always inside the declared input domain:

  * coeffs = [1.0, 2**53, 1.0, -2**53] -> np.sum gives 0.0, the exact signed
    total is 2.0 (the two 1.0s are absorbed by the 2**53 magnitude and cancel).
  * the windows `_spectral_helper` is actually fed: np.hanning(2048).sum() is
    1023.5000000000001 against an exact 1023.5; np.blackman(8192).sum() is
    3440.2200000000003 against an exact 3440.22.

numpy's reduction is moreover PAIRWISE, so it does not even agree with a
sequential float fold (np.hanning(2048): 1023.5000000000001 pairwise vs
1023.5000000000007 sequential). Exactness is therefore not a property of the
callee at all, and a spec asserting it describes a function the repo does not
contain. What the callee DOES guarantee is the classical accumulation error
bound, which is what the model now states and this script now checks.

The bound is deliberately the textbook one (`n * 2u * sum|x|` with u = 2**-53),
not a tightened fit to numpy's pairwise blocking: it is honest for any summation
order the callee may use, so the spec does not become hostage to a numpy
implementation detail. It is also enormously tighter than the defect it must
exclude — see the discrimination check below.

It additionally asserts the *discrimination property* the fix relies on: on a
window with negative coefficients the patched primitive differs from the
pre-patch one by FAR MORE than the bound — `|np.abs(w).sum() - np.sum(w)|` is
orders of magnitude above `roundoff_bound(w)` — so the model (signed total,
within roundoff) and the prepatch (magnitude total) genuinely diverge and the
tolerance cannot absorb the bug. This is what makes the spec see the bug
(G-DIFF) sound rather than vacuous. On the real scipy flattop windows the ratio
of the signed-vs-magnitude gap to the tolerance is ~1e10 to ~1e13.

Imports only `numpy` — the same library the gold patch calls. Exit 0 iff every
obligation holds.
"""
import random
import sys
from fractions import Fraction

import numpy as np

# One unit of relative rounding for a binary64 significand is u = 2**-53; the
# model's bound carries 2u = 2**-52 (Solution.lean `pure` region).
ULP_SCALE = Fraction(1, 2 ** 52)

# THE FOUR (unit roundoff, finite range) PAIRS the model quantifies over --
# `RealArith` in the `pure` region -- read back off numpy's own `finfo` so this
# script cannot drift from the formats the reduction is actually carried in.
# An earlier revision of this file exercised ONLY the binary64 pair, so it could
# not observe the accuracy claim at any other arithmetic the precondition admits;
# every pair is now checked.
def _pairs():
    out = []
    for dt in (np.float16, np.float32, np.float64, np.longdouble):
        fi = np.finfo(dt)
        p = fi.nmant + 1                                   # significand bits
        u = Fraction(1, 2 ** p)                            # unit roundoff
        rng = (Fraction(2) ** fi.maxexp) * (1 - Fraction(1, 2 ** p))
        out.append((np.dtype(dt).name, dt, u, rng))
    return out


REAL_ARITHS = _pairs()


def exact_of(v):
    """Exact rational of a numpy float scalar of ANY width.

    `float()` TRUNCATES a longdouble and manufactures spurious violations, so
    the wide format goes through `frexp` instead.
    """
    v = np.asarray(v)
    if v.dtype == np.longdouble:
        if not np.isfinite(v):
            return None
        m, e = np.frexp(v)
        mi = np.longdouble(m) * np.longdouble(2) ** 64
        return Fraction(int(mi), 2 ** 64) * (Fraction(2) ** int(e))
    f = float(v)
    if f != f or f in (float('inf'), float('-inf')):
        return None
    return Fraction(*f.as_integer_ratio())


def to_fmt(c, dt):
    """Exact rational -> nearest value of dt, preserving the exponent."""
    if dt != np.longdouble:
        return np.array(float(c), dtype=dt)
    n, d = c.numerator, c.denominator
    if n == 0:
        return np.longdouble(0)
    sh = n.bit_length() - d.bit_length()
    if sh > 0:
        d <<= sh
    else:
        n <<= -sh
    q = np.longdouble(n) / np.longdouble(d)
    return q * np.longdouble(2.0) ** sh


def check_all_ariths(coeffs):
    """The A-reference at EVERY real (ulp, maxMag) pair, not just binary64.

    `Accumulable maxMag ulp coeffs` is the model's precondition; where it fails
    the model makes NO claim, so the observation is skipped rather than asserted.
    """
    checked = 0
    for name, dt, u, rng in REAL_ARITHS:
        # mapping.md §2 maps an ARRAY ELEMENT to the `Rat` that is its exact
        # value, so the model's coeffs are read BACK OFF the built array. Taking
        # them from the pre-conversion rationals would compare the reduction of
        # one input against the exact total of a different one wherever the
        # format cannot hold the drawn value.
        arr = np.array([to_fmt(c, dt) for c in coeffs], dtype=dt)
        exact = [exact_of(v) for v in arr]
        if any(e is None for e in exact):
            continue                       # drawn value out of range for this fmt
        mag = mag_sum(exact)
        total = list_sum(exact)
        bound = Fraction(len(exact)) * (2 * u) * mag
        if mag + bound > rng:
            continue                       # precondition excludes: no claim made
        obs = exact_of(arr.sum())
        assert obs is not None, (
            "%s: `Accumulable` admitted %r but the real reduction saturated; the "
            "precondition does not bound the accumulation it claims to"
            % (name, exact))
        assert total - bound <= obs <= total + bound, (
            "WithinRoundoff unsound at the %s pair (ulp=%s) on %r: the real "
            "reduction gave %r, exact signed total %r, bound %r"
            % (name, u, exact, float(obs), float(total), float(bound)))
        checked += 1
    return checked


# --- model.py reference encoding (kept in lock-step with the `pure` region) ---

def list_sum(coeffs):
    """Reference encoding of the deep model `listSum`: the order-preserving
    SIGNED total (front-recursive: x + list_sum xs). Computed over exact
    Fractions so the reference side carries no rounding."""
    acc = Fraction(0)
    for x in coeffs:
        acc = acc + x
    return acc


def mag_sum(coeffs):
    """Reference encoding of the deep model `magSum`: the magnitude scale
    `sum |x_i|`, exact."""
    acc = Fraction(0)
    for x in coeffs:
        acc = acc + (-x if x < 0 else x)
    return acc


def roundoff_bound(coeffs):
    """Reference encoding of the deep model `roundoffBound`: the accuracy the
    reported total is guaranteed to, `n * 2u * sum|x_i|`, exact."""
    return Fraction(len(coeffs)) * ULP_SCALE * mag_sum(coeffs)


def within_roundoff(coeffs, out):
    """Reference encoding of the deep model's postcondition `WithinRoundoff`."""
    total = list_sum(coeffs)
    bound = roundoff_bound(coeffs)
    return total - bound <= out <= total + bound


def has_material_negative_content(coeffs):
    """True iff this window's negative lobes are large enough that the signed
    and magnitude totals differ by MORE than the accumulation error bound —
    i.e. iff the discrimination the fix relies on is observable here at all.

    This guard is load-bearing and was measured, not assumed. A window may
    contain negative samples that are pure floating-point dust rather than real
    lobes: np.blackman(8192) has samples of order -1e-19 whose total negative
    content is ~8e-21 of the window's magnitude scale, which is BELOW the
    accumulation error bound for a window of that length. On such a window
    `np.abs(w).sum()` and `w.sum()` are indistinguishable to any float
    summation, so demanding that they differ by more than the bound would be
    asserting something FALSE of the real callee. The windows that carry the
    fix's discriminating content — the cosine-sum flattops, and every explicit
    mixed-sign boundary case — have negative content of order 1e-1 to 1e-2 of
    the magnitude scale, i.e. 8 to 12 orders of magnitude above this threshold,
    so nothing that actually discriminates is excluded. Measured negative/magnitude
    ratios: flattop cosine-sum ~7.1e-2 at every length, mixed boundary cases
    2.9e-1 to 1.0, versus 0 for hanning/hamming/bartlett/kaiser and 8.1e-21 for
    blackman(8192).
    """
    mag = mag_sum(coeffs)
    if mag == 0:
        return False
    negative_content = sum((-x for x in coeffs if x < 0), Fraction(0))
    # The gap between the totals is exactly 2 * (negative content); require it
    # to clear the bound with room to spare.
    return 2 * negative_content > roundoff_bound(coeffs)


# --- the checks --------------------------------------------------------------

def check_sum_reference(coeffs):
    """Assert the REAL numpy window.sum() satisfies the deep model's
    postcondition at this window."""
    window = np.array([float(x) for x in coeffs], dtype=float)
    observed = float(window.sum())                 # real callee (patched prim)
    assert np.isfinite(observed), (
        "test window %r overflowed float64; not a well-posed observation"
        % (coeffs,))
    assert within_roundoff(coeffs, Fraction(observed)), (
        "WithinRoundoff unsound on %r: numpy window.sum() gave %r, exact signed "
        "total is %r, bound is %r (error %r exceeds it)"
        % (coeffs, observed, float(list_sum(coeffs)),
           float(roundoff_bound(coeffs)),
           float(abs(Fraction(observed) - list_sum(coeffs)))))


def check_discrimination(coeffs):
    """On a window with a negative coefficient, the patched primitive (signed
    sum) must differ from the pre-patch one (magnitude sum) by MORE than the
    accuracy bound; otherwise the tolerance in the spec could absorb the bug and
    the spec could not see it."""
    window = np.array([float(x) for x in coeffs], dtype=float)
    signed = float(window.sum())                   # patched: window.sum()
    magnitude = float(np.abs(window).sum())        # pre-patch: np.abs(w).sum()
    bound = roundoff_bound(coeffs)
    gap = abs(Fraction(magnitude) - Fraction(signed))
    assert gap > bound, (
        "discrimination property failed on %r: the signed/magnitude gap %r does "
        "NOT exceed the accuracy bound %r, so the spec's tolerance would admit "
        "the pre-patch magnitude total" % (coeffs, float(gap), float(bound)))
    # The magnitude total must also be OUTSIDE the model's postcondition — this
    # is the precise sense in which the prepatch violates the repaired spec.
    assert not within_roundoff(coeffs, Fraction(magnitude)), (
        "the magnitude total %r satisfies WithinRoundoff on %r; the spec would "
        "not reject the pre-patch reading" % (magnitude, coeffs))


def dyadic(rng):
    """An exactly-float-representable rational: integer numerator over a power
    of two. Element-wise exactness does NOT make the reduction exact (that was
    the retracted claim), but it keeps the reference total itself free of
    representation error, so the bound check measures only the accumulation."""
    num = rng.randint(-1024, 1024)
    den = 2 ** rng.randint(0, 6)
    return Fraction(num, den)


def wide_dynamic_range(rng):
    """A coefficient drawn to STRESS the accumulation: exponents spread widely
    enough that intermediate rounding is severe and cancellation is common. This
    is the domain the old fuzz missed entirely."""
    return Fraction(rng.choice([1, -1]) * 2 ** rng.randint(-60, 60))


def main():
    # Boundary windows over signs and the F2P flattop coefficient pattern.
    flattop_coeffs = [Fraction(c) for c in
                      [Fraction(21557895, 100000000), Fraction(41663158, 100000000),
                       Fraction(277263158, 1000000000), Fraction(83578947, 1000000000),
                       Fraction(6947368, 1000000000)]]
    # A real flattop-like window has NEGATIVE samples; the standard cosine-sum
    # construction with alternating-sign coefficients produces them. Use a small
    # explicit mixed-sign window standing in for that pattern.
    flattop_like = [Fraction(1), Fraction(-1, 4), Fraction(-3, 8),
                    Fraction(1, 2), Fraction(-1, 8)]

    # THE G-PANEL-2 WITNESS, now a permanent boundary case: the exact total is 2
    # but the real reduction returns 0.0. The old exactness assertion FAILED
    # here; the postcondition the model now states holds (|0 - 2| = 2 <= 16).
    catastrophic_cancellation = [Fraction(1), Fraction(2 ** 53),
                                 Fraction(1), Fraction(-(2 ** 53))]

    boundary = [
        [],                                  # empty window
        [Fraction(0)],                       # single zero
        [Fraction(3)],                       # single positive
        [Fraction(-3)],                      # single negative
        [Fraction(1), Fraction(2), Fraction(3)],            # all positive
        [Fraction(-1), Fraction(-2), Fraction(-3)],         # all negative
        [Fraction(1), Fraction(-1)],                        # cancels to zero
        [Fraction(5), Fraction(-2), Fraction(7), Fraction(-3)],  # mixed
        flattop_coeffs,
        flattop_like,
        [Fraction(0), Fraction(0), Fraction(0)],            # all-zero sentinel
        catastrophic_cancellation,                          # the panel witness
    ]
    all_arith_obs = 0
    for coeffs in boundary:
        check_sum_reference(coeffs)
        all_arith_obs += check_all_ariths(coeffs)

    # The discrimination property holds on every mixed/negative window above
    # whose signed and magnitude totals actually differ.
    for coeffs in boundary:
        if has_material_negative_content(coeffs):
            check_discrimination(coeffs)

    # The REAL windows `_spectral_helper` is fed. These are exactly the inputs
    # the retracted exactness claim broke on, so they are checked explicitly.
    for arr in (np.hanning(2048), np.hanning(256),
                np.blackman(8192), np.blackman(512),
                np.hamming(1024), np.bartlett(2048),
                np.kaiser(2048, 8.6)):
        coeffs = [Fraction(v) for v in arr.tolist()]
        check_sum_reference(coeffs)
        all_arith_obs += check_all_ariths(coeffs)
        # Most of these windows are all-nonnegative up to float dust, so the
        # discrimination is NOT observable on them; the guard says so.
        if has_material_negative_content(coeffs):
            check_discrimination(coeffs)

    # A cosine-sum flattop with negative lobes, built the way the F2P test does,
    # at several lengths — the discriminating window class for this fix.
    for n in (64, 512, 2048):
        a = [0.21557895, 0.41663158, 0.277263158, 0.083578947, 0.006947368]
        fac = np.linspace(-np.pi, np.pi, n)
        win = np.zeros(n)
        for k in range(len(a)):
            win += a[k] * np.cos(k * fac)
        coeffs = [Fraction(v) for v in win.tolist()]
        check_sum_reference(coeffs)
        all_arith_obs += check_all_ariths(coeffs)
        check_discrimination(coeffs)

    # --- randomized fuzz: numpy window.sum() satisfies WithinRoundoff --------
    rng = random.Random(25122)
    for _ in range(20000):
        n = rng.randint(0, 32)
        coeffs = [dyadic(rng) for _ in range(n)]
        check_sum_reference(coeffs)
        if n <= 8:                     # keep the wide-format arms affordable
            all_arith_obs += check_all_ariths(coeffs)
        # whenever the fuzz window has a negative coefficient AND the signed and
        # magnitude totals differ, the discrimination property must hold.
        if has_material_negative_content(coeffs):
            check_discrimination(coeffs)

    # --- the fuzz the OLD domain was too small to reach ---------------------
    # Long windows and wide exponent ranges, where the accumulation error is
    # large and cancellation is catastrophic. This is what makes the bound claim
    # a real check rather than an artifact of a tiny domain.
    for _ in range(20000):
        n = rng.randint(0, 400)
        coeffs = [wide_dynamic_range(rng) for _ in range(n)]
        window = np.array([float(x) for x in coeffs], dtype=float)
        if not np.isfinite(float(window.sum())):
            continue                              # overflow: not well-posed
        check_sum_reference(coeffs)

    print("G-AX OK: numpy window.sum() satisfies the deep model's WithinRoundoff "
          "postcondition on %d boundary + 7 real windows + 3 cosine-sum flattops "
          "+ 40000 fuzz windows (20000 of them wide-dynamic-range); "
          "discrimination (the signed/magnitude gap EXCEEDS the accuracy bound, "
          "so the magnitude total violates the postcondition) holds on every "
          "negative-coefficient window. The postcondition additionally holds at "
          "EVERY real (ulp, maxMag) pair `RealArith` admits -- float16/2**-11, "
          "float32/2**-24, float64/2**-53, longdouble/2**-64 -- over %d "
          "(window, arithmetic) observations, each in exact rational arithmetic, "
          "and `Accumulable` never admitted an input whose real reduction "
          "saturated." % (len(boundary), all_arith_obs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
