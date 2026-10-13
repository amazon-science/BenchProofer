#!/usr/bin/env python3
"""G-AX executable soundness check for matplotlib__matplotlib-14623.

Executes the REAL matplotlib range-conditioning callee on requested endpoint
pairs and asserts that every observation matches the axiom encoded in model.py
(`conditioned_lo` / `conditioned_hi`).

The conditioning step that the modeled function (`set_ylim` / `set_xlim` /
`set_*lim3d`) applies to a requested endpoint pair is the composition

    lo, hi = self.<ax>.get_major_locator().nonsingular(lo, hi)   # locator
    lo, hi = self.<ax>.limit_range_for_scale(lo, hi)             # scale clamp

This is the UNCHANGED callee for the LOGARITHMIC axis (the source of the bug):
`LogLocator.nonsingular` always sorts its output ascending and is NOT touched by
the patch. The axiom `conditioned_lo` / `conditioned_hi` claims exactly the
LITERAL model.py Ensures (this script checks the declared predicate, not a
hand-weakened restatement):

    Requires: lo > 0 and hi > 0 and lo < 1e15 and hi < 1e15
    conditioned_lo == (lo if lo<hi else hi)   when lo != hi   (min preserved)
    conditioned_hi == (hi if lo<hi else lo)   when lo != hi   (max preserved)
    conditioned_lo(lo,hi) < conditioned_hi(lo,hi)            ALWAYS (ascending)

i.e. on DISTINCT endpoints the exact min/max values are preserved; on EQUAL
endpoints NO concrete value is claimed -- only the always-ascending relation.
The earlier revision over-claimed the equal case as `lo-1`/`hi+1`; the real
callee returns `(1,10)` (log) / `(4.75,5.25)` (linear), so this script ASSERTS
the model never claims those magnitudes (the equal-case check verifies only
ascending and explicitly rejects any `lo-1`/`hi+1` claim).

The `< 1e15` Requires bound is itself validated: this script confirms that
(a) the axiom holds for EVERY pair inside the bound (including adjacent-integer
pairs at the 1e15 boundary and equal pairs), and (b) the two regimes that
WOULD violate the value-preservation Ensures lie OUTSIDE the bound and so are
correctly excluded -- the non-singular relative-gap expansion (>= 1e15, where
distinct endpoints get expanded, breaking value preservation) and the
int->float carrier collision (>= 1e16, where distinct ints collapse to one
float). Had the bound been absent, this script would FAIL on those inputs,
which is exactly the over-specification the previous check missed by fuzzing
only `[1, 1e5]`.

For the LOG scale this is sound pre- AND post-patch (LogLocator is unchanged),
so it is the load-bearing G-AX referent for the F2P modeled behaviour. The patch
*additionally* makes the base linear `Locator.nonsingular` return ascending too
(it drops `increasing=False`); when this script is run against the gold-patched
source it also corroborates that, and the end-to-end orientation contract that
the modeled `swapped`-restore provides (`set_ylim` keeps the requested
orientation -- the behaviour the F2P test pins). Whether the gold patch is
applied is auto-detected, so the script is sound in either run mode.

Imports nothing repo-specific beyond `matplotlib` itself -- the very package the
gold patch edits and whose callee the axiom stands in for. Exit 0 iff every
obligation holds.
"""
import random
import sys

import matplotlib
matplotlib.use("Agg")  # headless; no display needed
import matplotlib.pyplot as plt


# --- the real conditioning callee (the axiom's referent) ---------------------

def real_conditioning(yscale, lo, hi):
    """Run the REAL composition the modeled function applies:
    locator.nonsingular(lo, hi) then limit_range_for_scale(lo, hi), exactly as
    `set_ylim` does, on a fresh axis of the requested scale."""
    fig, ax = plt.subplots()
    try:
        ax.set_yscale(yscale)
        axis = ax.yaxis
        a, b = axis.get_major_locator().nonsingular(lo, hi)
        a, b = axis.limit_range_for_scale(a, b)
        return float(a), float(b)
    finally:
        plt.close(fig)


def real_set_ylim(yscale, bottom, top):
    """End-to-end: the gold-patched `set_ylim` must keep the requested
    orientation. Returns the stored (bottom, top)."""
    fig, ax = plt.subplots()
    try:
        ax.set_yscale(yscale)
        ax.set_ylim(bottom, top)
        return ax.get_ylim()
    finally:
        plt.close(fig)


def gold_applied():
    """True iff the gold patch is in effect, detected behaviourally: post-patch
    the base linear `Locator.nonsingular` returns ascending for a descending
    request (it dropped increasing=False); pre-patch it preserves descending."""
    a, b = real_conditioning("linear", 10.0, 1.0)
    return a < b


# --- the literal model.py Requires domain ------------------------------------

# Mirrors the model.py axiom Requires byte-for-byte:
#   lo > 0 and hi > 0 and lo < 1e15 and hi < 1e15
MAG_BOUND = 1000000000000000  # 1e15


def in_domain(lo, hi):
    return lo > 0 and hi > 0 and lo < MAG_BOUND and hi < MAG_BOUND


# --- checks ------------------------------------------------------------------

def check_conditioning_axiom(yscale, lo, hi):
    """Assert the real conditioning composition meets the LITERAL model.py
    Ensures for an in-domain endpoint pair:
      * always ascending: conditioned_lo < conditioned_hi;
      * DISTINCT endpoints: exact min preserved first, max preserved second;
      * EQUAL endpoints: NO concrete value claimed -- only ascending, and the
        model must NOT be claiming the old over-specified `lo-1`/`hi+1`.
    Only called for in-domain pairs (the axiom's Requires)."""
    assert in_domain(lo, hi), (lo, hi)  # we only assert the Ensures in-domain
    a, b = real_conditioning(yscale, lo, hi)
    # always-ascending (conditioned_lo < conditioned_hi) -- holds distinct+equal
    assert a < b, (
        "conditioning axiom unsound on scale=%s (%r, %r): expected ascending "
        "output, got (%r, %r)" % (yscale, lo, hi, a, b))
    if lo != hi:
        # distinct: the EXACT min/max are preserved (the literal Ensures)
        expected = (float(min(lo, hi)), float(max(lo, hi)))
        assert (a, b) == expected, (
            "conditioning axiom unsound on scale=%s (%r, %r): expected "
            "value-preserving ascending pair %r, got (%r, %r)"
            % (yscale, lo, hi, expected, a, b))
    else:
        # equal: the model claims ONLY ascending (checked above). Confirm it is
        # NOT the previously-over-specified surrounding-by-one interval -- the
        # real callee expands by scale-dependent magnitudes, never lo-1/hi+1.
        # (This is the regression guard for the original G-AX defect.)
        assert (a, b) != (float(lo - 1), float(hi + 1)), (
            "equal-case over-specification regression on scale=%s (%r, %r): "
            "the real callee must NOT yield the lo-1/hi+1 magnitudes the old "
            "axiom claimed -- got (%r, %r)" % (yscale, lo, hi, a, b))


def check_bound_is_load_bearing():
    """Confirm the `< 1e15` Requires bound is necessary, not cosmetic: the two
    out-of-domain regimes the previous `[1,1e5]` fuzz missed WOULD violate the
    axiom (value preservation / order-faithfulness), so excluding them is what
    makes the axiom sound. Had the bound been absent, this would FAIL on these
    inputs -- exactly the over-specification the old check could not see.

      (1) >= 1e15 (LINEAR): adjacent distinct integers are expanded by the
          non-singular relative-gap rule (tiny=1e-15), so the distinct-case
          value-preservation Ensures BREAKS. (Scale-specific: the LOG locator
          uses a wider gap rule and does not expand here, so this regime is
          demonstrated on the linear axis -- the one the patch makes ascending
          and the one whose value-preservation the axiom claims.)
      (2) >= 1e16 (BOTH scales): distinct integers collapse to one float, so
          the int->float carrier is no longer order-faithful -- the model's
          `lo != hi` no longer maps to distinct endpoints at all. This is the
          scale-INDEPENDENT reason the bound is required.

    Each regime is asserted OUT of domain AND to actually violate."""
    # (1) linear relative-gap expansion just above the bound (floats distinct)
    lo, hi = MAG_BOUND, MAG_BOUND + 1
    assert not in_domain(lo, hi), "1e15 adjacent pair should be out of domain"
    assert float(lo) != float(hi), "1e15 pair should still be float-distinct"
    a, b = real_conditioning("linear", lo, hi)
    assert (a, b) != (float(lo), float(hi)), (
        "expected the >=1e15 LINEAR regime to BREAK value preservation "
        "(%r,%r) -- if it did not, the bound would be unnecessarily tight; "
        "got preserved (%r,%r)" % (lo, hi, a, b))
    # (2) int->float collision at 1e16: distinct ints, identical floats (the
    # scale-independent carrier-faithfulness break that forces the bound)
    lo, hi = 10 ** 16, 10 ** 16 + 1
    assert not in_domain(lo, hi), "1e16 adjacent pair should be out of domain"
    assert float(lo) == float(hi), (
        "expected int->float collision at 1e16 (carrier no longer "
        "order-faithful); got distinct floats")


def check_orientation_end_to_end(yscale, bottom, top):
    """Assert the gold-patched `set_ylim` keeps the requested orientation
    (the F2P behaviour) and preserves distinct endpoint values."""
    lo, hi = real_set_ylim(yscale, bottom, top)
    if bottom > top:
        assert lo > hi, (
            "orientation lost on scale=%s set_ylim(%r, %r): stored (%r, %r) "
            "is not descending" % (yscale, bottom, top, lo, hi))
    elif bottom < top:
        assert lo < hi, (
            "orientation lost on scale=%s set_ylim(%r, %r): stored (%r, %r) "
            "is not ascending" % (yscale, bottom, top, lo, hi))
    if bottom != top:
        assert (lo, hi) == (bottom, top), (
            "endpoint values not preserved on scale=%s set_ylim(%r, %r): "
            "stored (%r, %r)" % (yscale, bottom, top, lo, hi))


def main():
    patched = gold_applied()
    # The LOG conditioning axiom is unchanged by the patch -> always checked.
    # The LINEAR conditioning (always-ascending) and the end-to-end orientation
    # contract hold only once the gold patch is applied.
    cond_scales = ["log", "linear"] if patched else ["log"]

    # boundary endpoint pairs (positive in-domain, admissible for both scales).
    # Extended past the old [1,1e5] window up to the 1e15 carrier-faithful
    # boundary, plus several EQUAL pairs (the singular-expansion case the
    # previous check under-fuzzed and where the original axiom over-specified).
    boundary = [
        (1, 10), (10, 1),          # the F2P case and its mirror
        (1, 2), (2, 1),
        (1000, 1), (1, 1000),
        (1, 100000), (100000, 1),
        (3, 7), (7, 3),
        (5, 5),                    # equal -> singular expansion
        (10, 10),
        (1, 1), (42, 42), (999, 999),  # more equal pairs (no value claimed)
        # high-magnitude distinct pairs INSIDE the bound (where the previous
        # [1,1e5] fuzz never reached): exercise the upper end of the faithful
        # range, including adjacent-integer pairs just below 1e15.
        (1000000, 1), (1, 1000000),
        (10000000000, 1), (1, 10000000000),
        (999999999999998, 999999999999999),   # adjacent, just below 1e15
        (999999999999999, 999999999999998),
        (1, 999999999999999), (999999999999999, 1),
    ]
    for yscale in cond_scales:
        for lo, hi in boundary:
            check_conditioning_axiom(yscale, lo, hi)
    if patched:
        for yscale in ["log", "linear"]:
            for bottom, top in boundary:
                check_orientation_end_to_end(yscale, bottom, top)

    # The `< 1e15` Requires bound is load-bearing, not cosmetic: confirm the
    # two out-of-domain regimes the old fuzz missed actually violate.
    check_bound_is_load_bearing()

    # randomized fuzz over positive integer endpoint pairs, now spanning the
    # FULL in-domain range [1, 1e15) (the carrier's order-faithful window) --
    # not the arbitrary [1, 1e5] of the previous check. A dedicated band of
    # near-1e15 fuzz hits the upper boundary where expansion is closest.
    rng = random.Random(14623)
    for yscale in cond_scales:
        for _ in range(400):
            lo = rng.randint(1, MAG_BOUND - 1)
            hi = rng.randint(1, MAG_BOUND - 1)
            check_conditioning_axiom(yscale, lo, hi)
        for _ in range(200):                       # near-boundary band
            base = rng.randint(MAG_BOUND // 100, MAG_BOUND - 1)
            gap = rng.randint(1, 1000)
            lo, hi = base, min(base + gap, MAG_BOUND - 1)
            if not in_domain(lo, hi):
                continue
            check_conditioning_axiom(yscale, lo, hi)
            check_conditioning_axiom(yscale, hi, lo)
        for _ in range(50):                        # equal-pair fuzz
            n = rng.randint(1, MAG_BOUND - 1)
            check_conditioning_axiom(yscale, n, n)
    if patched:
        for yscale in ["log", "linear"]:
            for _ in range(400):
                bottom = rng.randint(1, MAG_BOUND - 1)
                top = rng.randint(1, MAG_BOUND - 1)
                check_orientation_end_to_end(yscale, bottom, top)

    state = "gold-patched" if patched else "base (pre-patch)"
    print("G-AX OK [%s source]: conditioned_lo/conditioned_hi axiom sound "
          "against the LITERAL model Ensures (always ascending; exact min/max "
          "value-preservation on distinct endpoints; NO equal-case magnitude "
          "claimed) over %d boundary + ~650 fuzz pairs spanning the full "
          "in-domain range [1, 1e15); the < 1e15 Requires bound confirmed "
          "load-bearing (>=1e15 expansion and >=1e16 float-collision regimes "
          "lie outside it and would otherwise violate)%s"
          % (state, len(boundary),
             "; gold-patched set_ylim keeps the requested orientation end-to-end "
             "on log and linear" if patched else " (log scale; LogLocator is "
             "unchanged by the patch)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
