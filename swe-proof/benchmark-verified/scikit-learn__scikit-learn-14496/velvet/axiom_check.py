#!/usr/bin/env python3
"""G-AX executable soundness check for scikit-learn__scikit-learn-14496.

This bundle has NO consumed axioms (the only callee touching the conditioned
result, `_validate_size`, is unchanged and captured as a `require`). The single
kind-A obligation is a DEEP-MODEL fidelity check (A-reference): the pure-region
deep model must equal the REAL Python conditioning expression the gold patch
runs,

    max(2, int(value * n_samples))                       # patched optics_.py

over the documented fraction domain `value in (0, 1]`.

WHAT THIS CHECK ASSERTS, AND WHY IT IS SHAPED THIS WAY
------------------------------------------------------
An earlier revision of this check modelled the whole expression in exact
rationals: `max(2, floor(Fraction(repr(value)) * n))`. That was UNFAITHFUL, and
the faithfulness panel produced the witness that proves it:

    value=0.7, n_samples=90   (an ordinary in-domain input; _validate_size passes)
      real repo:  0.7*90 == 62.99999999999999  ->  int(...) == 62  ->  62
      old model:  Fraction('0.7')*90 == 63 exactly ->  floor == 63  ->  63

The scaling `value * n_samples` happens in IEEE double, BEFORE the truncation,
and its rounding can move the product across an integer boundary in EITHER
direction. No exact-rational surrogate for the product is faithful:

    value=0.7,  n=90   real 62, exact-decimal model 63   (model too high)
    value=0.03, n=100  real  3, exact-double  model  2   (model too low)

So the model does NOT recompute the product. `Solution.lean` takes the scaled
value as an INPUT (`scaled`) and constrains it with `scaledFromPopulation`, a
relative-precision band of one part in 2^53 around the ideal product — the
guarantee IEEE multiplication actually honors. What the model pins EXACTLY is
the part that IS exact: reducing that scaled value to a whole count and clamping
it at two.

This check therefore asserts:

  (1) THE BAND IS SOUND: the real machine product `fl(value * n)` always lies
      inside `scaledFromPopulation`'s band around the ideal product. This is the
      precondition the repo must satisfy for the contract to apply to it; if it
      ever failed, the spec would be vacuous on real inputs.

  (2) THE TRUNCATION IS EXACT: for the real machine product, the model's
      `max(2, Rat.floor(scaled))` equals the repo's `max(2, int(value * n))`
      EXACTLY — on every input, with NO tolerated divergences. This is the
      A-reference leg, and it includes the panel's witness (0.7 @ 90) and the
      F2P values (0.1, 0.08 @ n=31).

  (3) THE PREPATCH IS STILL DISCRIMINATED: wherever the machine product is
      non-integral, the pre-patch expression `max(2, value * n)` (no `int()`)
      differs from the model — the behaviour G-DIFF sees.

Imports stdlib only. Exit 0 iff every assertion holds.
"""
import math
import random
import sys
from fractions import Fraction

# `scaledFromPopulation`'s relative half-width (Solution.lean: 9007199254740992
# == 2^53), the relative precision IEEE double multiplication guarantees.
REL = Fraction(1, 2**53)


def exact_product(value_float, n):
    """The IDEAL product, as an exact rational: the true value of the double
    `value_float` times the integer `n`, with no rounding."""
    return Fraction(value_float) * n


def scaled_in_band(value_float, n):
    """(1) `scaledFromPopulation scaled value population` for the REAL machine
    product — the precondition the repository's own arithmetic must satisfy."""
    ideal = exact_product(value_float, n)
    scaled = Fraction(value_float * n)          # fl(value * n): what the repo has
    slack = REL * ideal
    return ideal - slack <= scaled <= ideal + slack


def model_count(value_float, n):
    """`asAbsoluteCount` (fraction branch) applied to the scaled value the REAL
    routine produces: max(2, Rat.floor scaled)."""
    scaled = Fraction(value_float * n)
    return max(2, math.floor(scaled))


def real_patched(value_float, n):
    """The gold patch's conditioning op, on the real IEEE float."""
    return max(2, int(value_float * n))


def prepatch_value(value_float, n):
    """Pre-patch conditioning value, before any int(): max(2, value*n)."""
    return max(2.0, value_float * n)


def main():
    # --- the faithfulness panel's witness, and the F2P inputs ----------------
    must_agree = [(0.7, 90), (0.1, 31), (0.08, 31),
                  (0.7, 170), (0.7, 180), (0.29, 100), (0.03, 100),
                  (0.6, 90), (0.5111111111111111, 90)]
    for v, n in must_agree:
        assert scaled_in_band(v, n), (
            "band UNSOUND at value=%r n=%r: the real machine product is outside "
            "scaledFromPopulation" % (v, n))
        assert real_patched(v, n) == model_count(v, n), (
            "named input value=%r n=%r: real %r != model %r"
            % (v, n, real_patched(v, n), model_count(v, n)))

    boundary = must_agree + [
        (0.1, 30), (0.08, 30), (1.0, 50), (0.5, 2), (0.5, 4), (0.5, 5),
        (0.01, 3), (0.01, 1000), (0.999999, 7), (0.25, 8), (0.75, 8),
        (1.0, 1), (1.0, 8000), (5e-324, 8000), (1e-300, 10 ** 6),
    ]

    rng = random.Random(14496)
    nice = [(rng.randint(1, 100) / 100.0, rng.randint(2, 8000))
            for _ in range(60000)]
    uniform = [(rng.uniform(1e-6, 1.0), rng.randint(1, 8000))
               for _ in range(60000)]
    # inputs whose IDEAL product is an integer — the class the old exact-rational
    # model got wrong, and the class the panel's witness came from.
    ties = []
    for _ in range(20000):
        n = rng.randint(2, 8000)
        k = rng.randint(1, n)
        ties.append((k / n, n))

    band_ok = 0
    agree = 0
    discriminated = 0
    for v, n in boundary + nice + uniform + ties:
        if not (0 < v <= 1):
            continue
        # (1) the band must contain the real machine product, always.
        assert scaled_in_band(v, n), (
            "band UNSOUND at value=%r n=%r: fl(value*n)=%r outside the 2^-53 "
            "relative band around the ideal product" % (v, n, v * n))
        band_ok += 1

        # (2) the truncation is EXACT — no tolerated divergences.
        real = real_patched(v, n)
        model = model_count(v, n)
        assert real == model, (
            "A-reference BROKEN at value=%r n=%r: real max(2,int(value*n))=%r "
            "but model max(2,floor(scaled))=%r" % (v, n, real, model))
        agree += 1

        # (3) the prepatch expression is discriminated wherever the machine
        #     product is non-integral (that is where the missing int() shows).
        pre = prepatch_value(v, n)
        if pre != int(pre):
            assert pre != real, (
                "prepatch not discriminated at value=%r n=%r" % (v, n))
            discriminated += 1

    print("G-AX OK: (1) the real machine product fl(value*n) lies inside "
          "scaledFromPopulation's 2^-53 relative band on all %d inputs; "
          "(2) the deep model max(2, Rat.floor scaled) == real "
          "max(2, int(value*n)) EXACTLY on all %d inputs, with NO tolerated "
          "divergences — including the faithfulness witness (0.7 @ 90 -> 62) "
          "and the F2P values (0.1/0.08 @ n=31); (3) the pre-patch expression "
          "is discriminated at all %d inputs with a non-integral product."
          % (band_ok, agree, discriminated))
    return 0


if __name__ == "__main__":
    sys.exit(main())
