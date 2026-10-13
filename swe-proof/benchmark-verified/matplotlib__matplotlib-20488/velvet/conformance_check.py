#!/usr/bin/env python3
"""G-CONF differential conformance for matplotlib__matplotlib-20488.

Band: float-precision (plan §10 Q1).

Refutes the R/I refinement leg (A3-A4: the modeled LogNorm lower-bound clamp
`eps if sVmin <= 0 else sVmin`).

ORACLE CHOICE — why we transliterate the source line instead of running
`_make_image`:
  The patched clamp lives inside `_ImageBase._make_image`, which requires a live
  Figure/Axes, a resampled masked numpy array, a configured LogNorm, and the
  full image-rendering pipeline. The behavior under test is the pure scalar
  clamp that sanitises the lower scale bound `s_vmin` before it is handed to a
  LogNorm. So, per the worker prompt, the ORACLE is the patched source line
  transliterated VERBATIM:
      s_vmin = np.finfo(scaled_dtype).eps if s_vmin <= 0 else s_vmin
  (from the gold-patched lib/matplotlib/image.py, `_make_image`, inside the
  `isinstance(self.norm, mcolors.LogNorm)` branch). The SHADOW is the modeled
  clamp from Solution.lean's `logNormVmin` post-image. We differential-test
  SHADOW vs ORACLE over fuzzed floats (incl. 0.0, -0.0, tiny, negative, large,
  and NaN) with eps > 0. Exit 0 iff zero disagreements. stdlib only.

  CALLEE ABSTRACTION: `np.finfo(scaled_dtype).eps` is a fixed strictly-positive
  machine-epsilon constant, UNCHANGED by the patch and identical on both sides
  of the fix. It is abstracted as the `eps` input here (mapping.md §4) and fuzzed
  over eps > 0 — there is no axiom and no axiom_check.py.

FLOAT MODEL NOTE (mapping.md §2): Solution.lean models s_vmin/eps as exact Rat,
because the discriminating behaviour is order-only (the `<= 0` boundary), which
is precision-independent. The clamp SELECTS between eps and s_vmin; it never
arithmetically combines them. Hence the observable-equality predicate here is
EXACT on the selection outcome (no ULP tolerance needed). Round-tripping
Lean<->Python floats is not lossy for this predicate because the comparison
`s_vmin <= 0` is exact for every non-NaN float, and NaN is handled explicitly
below.

NaN BEHAVIOUR (documented, plan §10 Q1): the patch condition `s_vmin <= 0` is
`False` for NaN in Python/numpy, so a NaN lower bound is left UNTOUCHED by both
the buggy and the fixed code. The Rat model has no NaN; this input is outside
the model's domain, and the model never claims to clamp NaN (its `sVmin <= 0`
clause does not fire when the comparison is False). We include NaN cases and
assert SHADOW == ORACLE (both pass NaN through, compared via repr to handle the
NaN != NaN identity).
"""
import math
import random
import struct
import sys

SEED = 20488
N_FUZZ = 200_000

# np.finfo eps values for the two scaled dtypes _make_image uses
# (np.float32 / np.float64). Both strictly positive.
EPS_F32 = 1.1920929e-07
EPS_F64 = 2.220446049250313e-16


def shadow(s_vmin, eps):
    """logNormVmin transliterated: the modeled LogNorm lower-bound clamp.
    Mirrors `if sVmin <= 0 then eps else sVmin` exactly."""
    if s_vmin <= 0:
        return eps
    return s_vmin


def oracle(s_vmin, eps):
    """The patched source line, transliterated verbatim from
    lib/matplotlib/image.py (gold-patched _make_image, LogNorm branch):
        s_vmin = np.finfo(scaled_dtype).eps if s_vmin <= 0 else s_vmin
    (`eps` stands in for the abstracted np.finfo(scaled_dtype).eps constant.)"""
    return eps if s_vmin <= 0 else s_vmin


def eq(a, b):
    """Exact equality on the selection outcome, NaN-aware.
    Both sides only ever return one of their inputs verbatim (no arithmetic), so
    bit-exact comparison is correct; we compare NaN by identity-of-payload via
    repr so that a NaN passed through on both sides counts as agreement."""
    if isinstance(a, float) and isinstance(b, float):
        if math.isnan(a) and math.isnan(b):
            return True
    return a == b


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    cases = []
    # Boundary / sentinel cases. -0.0 <= 0 is True in Python (so it clamps);
    # NaN <= 0 is False (so it passes through). Both must agree shadow==oracle.
    sentinels = [
        0.0, -0.0, 1.0, -1.0,
        1e-300, -1e-300, 5e-324,            # tiny pos/neg, smallest subnormal
        1e20, -1e20, 1e308, -1e308,         # large magnitudes
        float("nan"), float("inf"), float("-inf"),
    ]
    for sv in sentinels:
        for ep in (EPS_F32, EPS_F64, 1e-30, 0.5):
            cases.append((sv, ep))

    # Fuzz: random floats across many scales (incl. negatives, zero-ish),
    # eps drawn strictly positive.
    def rand_float():
        kind = rng.random()
        if kind < 0.15:
            return 0.0
        if kind < 0.30:
            return -0.0
        if kind < 0.40:
            # bit-pattern fuzz (may yield NaN/inf/subnormal)
            return struct.unpack("<d", struct.pack("<Q", rng.getrandbits(64)))[0]
        # scaled random across a wide exponent range, both signs
        m = rng.uniform(-1.0, 1.0)
        e = rng.randint(-320, 300)
        try:
            return m * (10.0 ** e)
        except OverflowError:
            return m * float("inf")

    for _ in range(N_FUZZ):
        sv = rand_float()
        # eps strictly positive (the require)
        ep = rng.choice((EPS_F32, EPS_F64)) * rng.uniform(0.5, 1e6)
        if not (ep > 0):
            ep = EPS_F64
        cases.append((sv, ep))

    for s_vmin, eps in cases:
        count += 1
        s = shadow(s_vmin, eps)
        o = oracle(s_vmin, eps)
        if not eq(s, o):
            disagreements.append((s_vmin, eps, s, o))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s): %r"
              % (len(disagreements), disagreements))
        return 1
    print("G-CONF OK: R/I shadow of logNormVmin agrees with the patched source "
          "line on %d (s_vmin, eps) pairs (boundary + sentinel + fuzz, "
          "seed=%d, eps>0), 0 disagreements. NaN/-0.0/inf/subnormal covered; "
          "np.finfo(...).eps abstracted as the eps input."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
