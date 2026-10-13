#!/usr/bin/env python3
"""G-CONF differential conformance check for matplotlib__matplotlib-25122
(plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo type (a `numpy` window array), via
              the mapping.md bijection (`List Rat` ↔ ordered coefficients,
              `coeffs[k]` ↔ `w[k]`). The impl's fold `listSum` / backward
              `while` loop is the order-preserving SIGNED total; it is
              transliterated EXACTLY, over `fractions.Fraction`, because the Lean
              carrier is exact `Rat` and that is what the impl computes.
  * ORACLE  — `patch.diff`'s behaviour: the patched normalization primitive
              `window.sum()` (the real `numpy` reduction the gold patch
              introduces at `lib/matplotlib/mlab.py:403/430`).

WHAT AGREEMENT MEANS HERE (audit correction, G-PANEL-2). An earlier revision
compared these two for BIT EQUALITY, with the shadow computed as a sequential
float fold, and asserted the two were bit-identical on the fuzz domain. That was
wrong twice over, and both errors are now fixed:

  1. The exact rational total and the float reduction are NOT equal in general.
     On coeffs = [1.0, 2**53, 1.0, -2**53] the reduction returns 0.0 while the
     exact total is 2.0. On the windows `_spectral_helper` actually receives,
     np.hanning(2048).sum() is 1023.5000000000001 against an exact 1023.5.
  2. numpy's reduction is PAIRWISE, so it is not even equal to a sequential
     float fold of the same values: np.hanning(2048) sums to 1023.5000000000001
     pairwise but 1023.5000000000007 sequentially. A shadow that fixed a
     summation order would therefore be unfaithful to the callee no matter how
     it rounded.

So the observable the spec pins — and the observable this check compares — is
the model's postcondition `WithinRoundoff`: the oracle's value must lie within
`roundoff_bound(coeffs) = n * 2**-52 * sum|x_i|` of the shadow's exact total.
That is the relation the gold patch's expression actually honors, for any
summation order, and it is the relation `Solution.lean` requires of `out`. A
disagreement is a window where the real reduction falls OUTSIDE the interval the
spec's postcondition allows — a genuine R/I-fidelity counterexample.

The bound is not a fudge factor that hides the fix: the check also verifies, on
every window with real negative lobes, that the PRE-PATCH expression
`np.abs(window).sum()` falls OUTSIDE the same interval. So the tolerance
separates the patched behaviour from the pre-patch behaviour rather than
blurring them, which is what makes G-DIFF's refutation of the prepatch sound.

Runs stdlib + numpy only (numpy is the library the patched code calls). The fuzz
seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys
from fractions import Fraction

import numpy as np

SEED = 25122
N_FUZZ = 100_000

# Solution.lean's bound carries 2u for a binary64 significand, u = 2**-53.
ULP_SCALE = Fraction(1, 2 ** 52)


# The four (unit roundoff, finite range) PAIRS the spec's `RealArith`
# precondition admits, read off numpy's own `finfo` so this shadow cannot drift
# from the formats the reduction is actually carried in. An earlier revision
# compared at the binary64 pair ONLY, so it could not observe the R/I leg at any
# other arithmetic the precondition admits.
def _real_ariths():
    out = []
    for dt in (np.float16, np.float32, np.float64, np.longdouble):
        fi = np.finfo(dt)
        p = fi.nmant + 1
        out.append((np.dtype(dt).name, dt, Fraction(1, 2 ** p),
                    (Fraction(2) ** fi.maxexp) * (1 - Fraction(1, 2 ** p))))
    return out


REAL_ARITHS = _real_ariths()


def exact_of(v):
    """Exact rational of a numpy float of ANY width (`float()` truncates the
    wide format and manufactures spurious disagreements)."""
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
    return (np.longdouble(n) / np.longdouble(d)) * np.longdouble(2.0) ** sh


def conform_all_ariths(coeffs):
    """The R/I leg at EVERY real (ulp, maxMag) pair. Returns (checked, failures).
    Where `Accumulable maxMag ulp coeffs` fails the spec makes no claim, so the
    observation is skipped rather than counted as agreement.

    The bridge direction matters and is easy to get backwards. mapping.md §2 maps
    a real window ARRAY ELEMENT to the `Rat` that is its EXACT value, so the
    model's `coeffs` are read BACK OFF the built array. Deriving the shadow total
    from the pre-conversion rationals instead compares the reduction of one input
    against the exact total of a DIFFERENT one, which reports spurious
    disagreements wherever the format cannot hold the drawn value (e.g. 2**-54 is
    below float16's smallest subnormal and lands on 0)."""
    checked, fails = 0, []
    for name, dt, u, rng in REAL_ARITHS:
        arr = np.array([to_fmt(c, dt) for c in coeffs], dtype=dt)
        exact = [exact_of(v) for v in arr]
        if any(e is None for e in exact):
            continue            # the drawn value itself is out of this format
        mag = shadow_mag_sum(exact)
        total = shadow_window_sum(exact)
        bound = Fraction(len(exact)) * (2 * u) * mag
        if mag + bound > rng:
            continue
        obs = exact_of(arr.sum())
        if obs is None:
            fails.append((name, exact, 'real reduction SATURATED though '
                                        '`Accumulable` admitted the input'))
            continue
        if not (total - bound <= obs <= total + bound):
            fails.append((name, exact,
                          'oracle %r outside [%r, %r]'
                          % (float(obs), float(total - bound),
                             float(total + bound))))
        checked += 1
    return checked, fails


# --- the R/I shadow: Solution.lean listSum / windowSum, transliterated -------
def shadow_window_sum(coeffs):
    """`listSum coeffs` transliterated to Python: the order-preserving SIGNED
    total of the coefficients (the backward `while` fold of windowSum computes
    exactly this). Computed over exact Fractions, because the Lean carrier is
    exact `Rat` — the impl region carries no rounding."""
    acc = Fraction(0)
    for x in coeffs:
        acc = acc + x
    return acc


def shadow_mag_sum(coeffs):
    """`magSum coeffs` transliterated: the magnitude scale, exact."""
    acc = Fraction(0)
    for x in coeffs:
        acc = acc + (-x if x < 0 else x)
    return acc


def shadow_roundoff_bound(coeffs):
    """`roundoffBound coeffs` transliterated: `n * 2u * sum|x_i|`, exact."""
    return Fraction(len(coeffs)) * ULP_SCALE * shadow_mag_sum(coeffs)


def shadow_within_roundoff(coeffs, out):
    """`WithinRoundoff coeffs out` transliterated — the spec's postcondition."""
    total = shadow_window_sum(coeffs)
    bound = shadow_roundoff_bound(coeffs)
    return total - bound <= out <= total + bound


def oracle_window_sum(coeffs):
    """patch.diff's behaviour: the patched normalization primitive
    `window.sum()` — the real numpy reduction the gold patch introduces (the
    `np.abs(...)` wrapper is removed)."""
    window = np.array([float(x) for x in coeffs], dtype=float)
    return float(window.sum())


def prepatch_window_sum(coeffs):
    """The PRE-PATCH expression `np.abs(window).sum()`, kept so the check can
    confirm the tolerance still SEPARATES the two behaviours."""
    window = np.array([float(x) for x in coeffs], dtype=float)
    return float(np.abs(window).sum())


def has_material_negative_content(coeffs):
    """True iff the negative lobes are large enough for the signed/magnitude
    distinction to be observable above the accumulation error. Windows whose
    only negative samples are float dust (e.g. np.blackman's ~-1e-19 tails) do
    NOT discriminate, and requiring them to would assert something false of the
    real callee."""
    if shadow_mag_sum(coeffs) == 0:
        return False
    negative_content = sum((-x for x in coeffs if x < 0), Fraction(0))
    return 2 * negative_content > shadow_roundoff_bound(coeffs)


def dyadic(rng):
    num = rng.randint(-1024, 1024)
    den = 2 ** rng.randint(0, 6)
    return Fraction(num, den)


def wide_dynamic_range(rng):
    """Exponents spread widely enough that the accumulation rounds hard and
    cancellation is catastrophic — the domain the old fuzz never reached."""
    return Fraction(rng.choice([1, -1]) * 2 ** rng.randint(-60, 60))


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4)
    yield []
    yield [Fraction(0)]
    yield [Fraction(3)]
    yield [Fraction(-3)]
    yield [Fraction(1), Fraction(2), Fraction(3)]
    yield [Fraction(-1), Fraction(-2), Fraction(-3)]
    yield [Fraction(1), Fraction(-1)]
    yield [Fraction(5), Fraction(-2), Fraction(7), Fraction(-3)]
    yield [Fraction(1), Fraction(-1, 4), Fraction(-3, 8),
           Fraction(1, 2), Fraction(-1, 8)]      # flattop-like (negative samples)
    # The G-PANEL-2 witness: the exact total is 2, the real reduction gives 0.0.
    yield [Fraction(1), Fraction(2 ** 53), Fraction(1), Fraction(-(2 ** 53))]
    # The real windows _spectral_helper is fed.
    for arr in (np.hanning(2048), np.blackman(8192), np.hamming(1024),
                np.bartlett(512), np.kaiser(2048, 8.6)):
        yield [Fraction(v) for v in arr.tolist()]
    # Cosine-sum flattops with genuine negative lobes, as the F2P test builds.
    for m in (64, 512, 2048):
        a = [0.21557895, 0.41663158, 0.277263158, 0.083578947, 0.006947368]
        fac = np.linspace(-np.pi, np.pi, m)
        win = np.zeros(m)
        for k in range(len(a)):
            win += a[k] * np.cos(k * fac)
        yield [Fraction(v) for v in win.tolist()]
    for i in range(n):
        k = rng.randint(0, 32)
        if i % 4 == 3:
            k = rng.randint(0, 400)
            yield [wide_dynamic_range(rng) for _ in range(k)]
        else:
            yield [dyadic(rng) for _ in range(k)]


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    skipped_overflow = 0
    separations = 0
    arith_obs = 0
    for coeffs in fuzz_inputs(N_FUZZ, rng):
        # the R/I leg at every real arithmetic the precondition admits, not just
        # binary64 (kept to short windows so the wide-format arms stay affordable)
        if len(coeffs) <= 8:
            n_ok, n_bad = conform_all_ariths(coeffs)
            arith_obs += n_ok
            for nm, cs, why in n_bad:
                disagreements.append((cs, 'pair=%s: %s' % (nm, why), None, None))
        oracle = oracle_window_sum(coeffs)
        if not np.isfinite(oracle):
            skipped_overflow += 1       # float64 overflow: not a well-posed obs
            continue
        count += 1
        # The R/I leg: the real reduction must satisfy the spec's postcondition
        # against the impl region's exact total.
        if not shadow_within_roundoff(coeffs, Fraction(oracle)):
            disagreements.append(
                (coeffs, float(shadow_window_sum(coeffs)), oracle,
                 float(shadow_roundoff_bound(coeffs))))
            if len(disagreements) >= 5:
                break
        # The tolerance must still SEPARATE patched from pre-patch wherever the
        # distinction is observable, else it would be blurring the fix away.
        if has_material_negative_content(coeffs):
            if shadow_within_roundoff(coeffs, Fraction(prepatch_window_sum(coeffs))):
                disagreements.append(
                    (coeffs, "prepatch np.abs(w).sum() satisfies the "
                             "postcondition — tolerance too loose",
                     prepatch_window_sum(coeffs),
                     float(shadow_roundoff_bound(coeffs))))
                if len(disagreements) >= 5:
                    break
            else:
                separations += 1
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for c, sh, orc, bound in disagreements:
            print("  input=%r shadow=%r oracle=%r bound=%r" % (c, sh, orc, bound))
        return 1
    print("G-CONF OK: the real `window.sum()` satisfies the spec's WithinRoundoff "
          "postcondition against the R/I shadow of windowSum on %d inputs "
          "(seed=%d), 0 disagreements; %d overflow inputs skipped; the pre-patch "
          "`np.abs(window).sum()` VIOLATES that same postcondition on all %d "
          "windows with material negative lobes, so the tolerance separates the "
          "patched behaviour from the bug. The R/I leg additionally holds at every "
          "real (ulp, maxMag) pair `RealArith` admits (float16/2**-11, "
          "float32/2**-24, float64/2**-53, longdouble/2**-64) over %d "
          "(window, arithmetic) observations in exact rational arithmetic."
          % (count, SEED, skipped_overflow, separations, arith_obs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
