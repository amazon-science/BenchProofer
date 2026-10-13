#!/usr/bin/env python3
"""G-AX executable soundness check for scikit-learn__scikit-learn-14496.

This bundle consumes NO `@ContractOnly` axiom: the operation the gold patch
changes -- wrapping the scaled, clamped neighbourhood value in `int(...)` -- is
modelled DEEPLY in model.py by a verified floor loop. G-AX therefore validates
that deep model (the A-reference) against the REAL changed operation, exactly as
the gold patch computes it.

MODEL BOUNDARY (the faithfulness-critical point). The repository computes the
scaled value `min_samples * n_samples` in IEEE-754 float64 BEFORE the changed
operation touches it; that multiplication is unchanged by the patch and sits
OUTSIDE the model. model.py therefore takes the repo-computed float64 product
`scaled` as its input (every float64 is an exact rational, carried losslessly
by --float-encoding=real) and models only what the patch changes: the
clamp-to-two and the reduction to a whole number. This check consequently
feeds BOTH sides the SAME float64 product -- the model is
floor(max(2.0, scaled)) on that double, the gold is max(2, int(scaled)) on
that same double -- so float64 rounding of the upstream multiply (e.g.
0.11165523996082272 * 1021 rounding UP to exactly 114.0) affects both sides
identically and the equality asserted here is exactly the equality that holds
in the real interpreter.

Two things are checked, with NO double-mask (the integrality the model decides
is asserted directly, not via a proxy that pre-filters both sides):

  (1) The deep floor model == the real gold operation on the shared float64
      product. We assert equality AND that the result is a genuine `int`
      (refinement.md note D ties the two placements of `int`). The model's
      `is_whole` postcondition is checked DIRECTLY by asserting the result is
      integral, not by comparing already-floored values on both sides.

  (2) The pre-patch value (the bug) is NOT integral on the discriminating F2P
      input -- so the spec's `is_whole` clause genuinely separates patch from
      bug (it is not vacuously satisfiable). We fail loud if any enumerated F2P
      case were accidentally skipped.

Imports nothing repo-specific: only `math` / `random` from the standard library.
The real operation under test (`int(...)`, `max(...)`, float multiply) is plain
Python arithmetic -- identical in the eval interpreter. Exit 0 iff sound.
"""
import math
import random
import struct
import sys


def _next_double_up(v):
    """The smallest double strictly greater than v (v finite, v >= 0).
    Bit-level equivalent of math.nextafter(v, inf), which the instance
    image's older Python lacks (nextafter is 3.9+)."""
    if v == 0.0:
        return 5e-324
    (bits,) = struct.unpack("<q", struct.pack("<d", v))
    return struct.unpack("<d", struct.pack("<q", bits + 1))[0]


def _next_double_down(v):
    """The largest double strictly smaller than v (v finite, v > 0)."""
    (bits,) = struct.unpack("<q", struct.pack("<d", v))
    return struct.unpack("<d", struct.pack("<q", bits - 1))[0]


def repo_scaled(fraction, n_samples):
    """The UPSTREAM (unchanged, out-of-model) float64 product exactly as the
    repository computes it: `min_samples * n_samples` in IEEE-754 float64."""
    return fraction * n_samples


def model_floor(scaled):
    """Reference of model.py's deep floor model: floor(max(2.0, scaled)),
    taking the repo-computed float64 product as its input."""
    clamped = max(2.0, scaled)
    return math.floor(clamped)


def gold_value(scaled):
    """The REAL gold operation on the same float64 product:
    max(2, int(scaled))."""
    return max(2, int(scaled))


def check_case(fraction, n_samples):
    scaled = repo_scaled(fraction, n_samples)   # ONE shared float64 product
    m = model_floor(scaled)
    g = gold_value(scaled)
    # (1a) deep model == real gold operation on the SAME float64 input
    #      (refinement.md note D)
    assert m == g, (
        "deep floor model != gold int-wrap on (frac=%r, n=%r, scaled=%r): "
        "model floor=%r, gold int=%r" % (fraction, n_samples, scaled, m, g))
    # (1b) the result is a genuine whole number (the `is_whole` postcondition),
    #      asserted DIRECTLY -- no double-mask.
    assert isinstance(m, int) and float(m) == m, (
        "model result not integral on (frac=%r, n=%r): %r" % (fraction, n_samples, m))
    # (1c) the floor relation the model pins: m <= clamped < m + 1, m >= 2.
    clamped = max(2.0, scaled)
    assert m >= 2, "model result below the floor of two: %r" % (m,)
    assert m <= clamped < m + 1, (
        "floor relation violated on (frac=%r, n=%r): %r not floor of %r"
        % (fraction, n_samples, m, clamped))
    return m


def main():
    # --- F2P inputs (sklearn/cluster/tests/test_optics.py::test_extract_xi) ---
    # X = vstack(C1..C5 [5 each], [[100,100]], C6 [5]) -> 31 samples.
    # min_samples=0.1  -> int(max(2, 0.1*31))  = int(max(2, 3.1))  = 3
    # min_cluster_size=0.08 -> int(max(2, 0.08*31)) = int(max(2, 2.48)) = 2
    f2p = [(0.1, 31), (0.08, 31)]
    f2p_expected = [3, 2]
    seen = []
    for (frac, n), exp in zip(f2p, f2p_expected):
        got = check_case(frac, n)
        assert got == exp, (
            "F2P expectation broken on (frac=%r, n=%r): got %r want %r"
            % (frac, n, got, exp))
        seen.append((frac, n))
    assert seen == f2p, "an F2P case was skipped (false pass guard)"

    # The bug must be visible: the pre-patch value is NOT integral on the
    # discriminating F2P input min_cluster_size=0.08 (-> 2.48), so `is_whole`
    # genuinely separates patch from bug.
    prepatch_val = max(2.0, repo_scaled(0.08, 31))   # = 2.48, the un-wrapped real
    assert float(prepatch_val).is_integer() is False, (
        "discriminator vacuous: pre-patch value %r is already integral"
        % (prepatch_val,))
    assert model_floor(repo_scaled(0.08, 31)) == 2, \
        "model must floor 2.48 -> 2 (not round/ceil)"

    # --- float64 ROUNDING boundary (the G-PANEL-2 counterexample) ------------
    # 0.11165523996082272 * 1021 rounds UP in float64 to EXACTLY 114.0 even
    # though the exact rational product is strictly below 114. Since the model
    # takes the repo-computed double, both sides see 114.0 and agree on 114.
    s = repo_scaled(0.11165523996082272, 1021)
    assert s == 114.0, "float64 rounding fixture drifted: %r" % (s,)
    assert model_floor(s) == gold_value(s) == 114, (
        "model boundary broken on the rounded-up product: model=%r gold=%r"
        % (model_floor(s), gold_value(s)))
    check_case(0.11165523996082272, 1021)
    # products that land just below / at / just above a whole double
    for k in (2, 3, 114, 1000):
        for v in (float(k),
                  _next_double_down(float(k)),
                  _next_double_up(float(k))):
            m = model_floor(v)
            g = gold_value(v)
            assert m == g, (
                "model != gold on near-whole double %r: %r vs %r" % (v, m, g))

    # --- boundary cases over the admitted domain 0 < frac <= 1, n >= 2 -------
    boundary = [
        (1.0, 2), (1.0, 3), (1.0, 100),     # frac = 1 (upper edge)
        (0.5, 2), (0.5, 3), (0.5, 4),       # product straddling 2
        (0.1, 20), (0.1, 21), (0.1, 25),    # product just above 2
        (0.01, 2), (0.001, 1000),           # tiny fraction -> clamp to 2
        (0.999999, 2), (0.5, 5),            # near-integer products
        (2.0 / 3.0, 3),                     # 2.0000000000000004 product
    ]
    for frac, n in boundary:
        check_case(frac, n)

    # --- randomized fuzz over the admitted domain ---------------------------
    rng = random.Random(14496)
    for _ in range(50000):
        frac = rng.uniform(1e-9, 1.0)
        n = rng.randint(2, 100000)
        check_case(frac, n)

    print("G-AX OK: deep floor model == real int(max(2, scaled)) on the SHARED "
          "repo-computed float64 product for %d F2P + 1 float64-rounding + %d "
          "boundary + 50000 fuzz inputs (incl. the 0.11165523996082272*1021 -> "
          "114.0 round-up); result integral and equal to the gold whole-number "
          "size; pre-patch (un-wrapped) value provably non-integral on the F2P "
          "discriminator." % (len(f2p), len(boundary)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
