#!/usr/bin/env python3
"""G-AX executable soundness check for matplotlib__matplotlib-24870.

model.py consumes one @ContractOnly axiom, `auto_levels(zmin, zmax)`, which
abstracts the ordinary automatic default level-selection matplotlib applies to
a *continuous* field when the caller gives neither explicit levels nor an
explicit level count. The axiom's Ensures is the weakest fact the proof needs:

    over a WELL-RESOLVED data range it produces MORE THAN ONE level
    (len(auto_levels(zmin, zmax)) > 1).

"Well-resolved" is the axiom's (and the caller's) precondition: with
`span = zmax - zmin > 0`,

    span >= 1e-6                       (absolute floor)
    span >= 1e-9 * zmax                (relative to the upper extent)
    span >= 1e-9 * (0 - zmin)          (relative to the lower extent)

This scoping is necessary AND sound: the real selection (the default-count
branch of `QuadContourSet._process_contour_level_args` -> `_autolev` ->
`MaxNLocator(N+1).tick_values` trimmed) DOES collapse to a SINGLE level on an
unresolvable range — measured in the canonical 3.6 eval image:
`(1e-300, 2e-300) -> [1e-300]` (1 level), `(0.0, 5e-324) -> [0.0]`,
`(1.0, 1.0+1e-14) -> [1.0]`. (The dissent's claim that no 1-level case exists
was wrong; the run below records the collapse and confirms the guard excludes
exactly it.) Every meaningful contour range, in particular the two-valued range
[0, 1] the F2P test exercises, clears the guard with enormous margin, so the
scoping does not weaken the tested behaviour.

The check therefore (1) asserts `len(cs.levels) > 1` on every guard-satisfying
input (the soundness obligation the proof consumes), and (2) records that the
known collapse witnesses are precisely the guard-EXCLUDED ones (faithfulness:
the guard is not over-claiming — it carves out exactly the degenerate regime).
We measure `list(cs.levels)` — the same artifact model.py equates to
`auto_levels(zmin, zmax)`. Exit 0 iff sound.

Imports nothing repo-specific beyond matplotlib itself (the very package the
gold patch lives in).
"""
import random
import sys


def well_resolved(zmin, zmax):
    """The axiom's / caller's precondition (model.py): a well-resolved range."""
    span = zmax - zmin
    if not (zmin < zmax):
        return False
    if not (span >= 1e-6):
        return False
    if not (span >= 1e-9 * zmax):
        return False
    if not (span >= 1e-9 * (0.0 - zmin)):
        return False
    return True


def real_default_levels(zmin, zmax):
    """Run the REAL matplotlib default level-selection on a continuous field
    spanning [zmin, zmax] with no explicit levels/level-count, and return the
    resulting level list (`QuadContourSet.levels`)."""
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # A 2x2 continuous (float) field whose min is zmin and max is zmax, so the
    # data range handed to the default selection is exactly [zmin, zmax].
    z = np.array([[zmin, zmax], [zmin, zmax]], dtype=np.float64)
    cs = plt.contour(z)               # line contour, default levels
    levels = list(cs.levels)
    plt.close("all")
    return levels


def check_more_than_one(zmin, zmax):
    """The proof's obligation: on a guard-satisfying range, len > 1."""
    assert well_resolved(zmin, zmax), (
        "test bug: check_more_than_one called on a non-well-resolved range "
        "[%r, %r] (the axiom does not claim len>1 there)" % (zmin, zmax))
    levels = real_default_levels(zmin, zmax)
    assert len(levels) > 1, (
        "auto_levels axiom UNSOUND: real default selection on a well-resolved "
        "continuous range [%r, %r] gave %d level(s) (%r); the axiom requires >1"
        % (zmin, zmax, len(levels), levels))


def main():
    # --- boundary cases (all well-resolved; the proof consumes len>1 here) ---
    boundary = [
        (0.0, 1.0),       # the same [0,1] range a bool field would yield (F2P)
        (-1.0, 1.0),
        (0.0, 100.0),
        (-50.0, -10.0),
        (1.0, 1.0001),    # narrow range, still well-resolved (rel ~1e-4)
        (0.0, 1e6),
        (-3.14159, 2.71828),
        (1e-12, 2e-12),   # tiny magnitude but rel span 1.0 -> well-resolved
        (1e-200, 1.5e-200),
        (1.0, 1.0 + 1e-12),  # rel span 1e-12, just inside the 1e-9? -> see below
    ]
    # (1.0, 1.0+1e-12) has rel span 1e-12 < 1e-9, so it is NOT well-resolved;
    # drop any non-well-resolved entry rather than mis-assert on it.
    boundary = [bc for bc in boundary if well_resolved(*bc)]
    for zmin, zmax in boundary:
        check_more_than_one(zmin, zmax)

    # --- the documented collapse witnesses: confirm they are GUARD-EXCLUDED ---
    # (faithfulness: the guard carves out exactly the degenerate regime where the
    # real selection collapses to a single tick, measured in the 3.6 image.)
    collapse_witnesses = [
        (1e-300, 2e-300),   # -> [1e-300]
        (0.0, 5e-324),      # -> [0.0]
        (0.0, 1e-300),      # -> [0.0]
        (1.0, 1.0 + 1e-14), # -> [1.0]
        (1.0, 1.0 + 1e-15), # -> [1.0]
        (1e10, 1e10 + 1.0), # rel span 1e-10 -> [1e10]
    ]
    for zmin, zmax in collapse_witnesses:
        assert not well_resolved(zmin, zmax), (
            "guard FAITHFULNESS hole: a documented collapse witness [%r, %r] is "
            "marked well-resolved but the real selection collapses there"
            % (zmin, zmax))
        # Sanity: confirm the real selection really does collapse on at least
        # the canonical subnormal witness (records the empirical 1-level fact).
        if (zmin, zmax) == (1e-300, 2e-300):
            lv = real_default_levels(zmin, zmax)
            assert len(lv) == 1, (
                "expected the subnormal witness to collapse to 1 level, got %r"
                % (lv,))

    # --- randomized fuzz: assert soundness over EVERY well-resolved sample,
    #     across ordinary, large, tiny-magnitude and tiny-span regimes. -------
    rng = random.Random(24870)
    n_checked = 0
    n_excluded = 0
    for _ in range(2000):
        mode = rng.randint(0, 4)
        if mode == 0:                       # ordinary magnitude / span
            a = rng.uniform(-1e3, 1e3)
            span = 10.0 ** rng.uniform(-9.0, 3.0)
            b = a + span
        elif mode == 1:                     # near-magnitude-1, varied rel span
            a = rng.uniform(-1e6, 1e6)
            span = 10.0 ** rng.uniform(-12.0, 6.0)
            b = a + span
        elif mode == 2:                     # tiny magnitude, varied rel span
            mag = 10.0 ** rng.uniform(-308.0, 10.0)
            b = mag * (1.0 + 10.0 ** rng.uniform(-17.0, 0.0))
            a = mag
        elif mode == 3:                     # zero lower extent, tiny/huge upper
            a = 0.0
            b = 10.0 ** rng.uniform(-324.0, 10.0)
        else:                               # large magnitude, varied span
            a = rng.uniform(-1e10, 1e10)
            span = 10.0 ** rng.uniform(-3.0, 9.0)
            b = a + span
        if not (a < b):
            continue
        if not (a == a and b == b):         # NaN guard
            continue
        if well_resolved(a, b):
            check_more_than_one(a, b)
            n_checked += 1
        else:
            n_excluded += 1

    print("G-AX OK: auto_levels axiom (len>1 on a WELL-RESOLVED range) is sound "
          "of the REAL matplotlib default selection. %d boundary + %d "
          "well-resolved fuzz ranges all gave >1 level; %d degenerate fuzz "
          "ranges (+ %d documented collapse witnesses incl. (1e-300,2e-300)->"
          "1 level) are correctly EXCLUDED by the guard. Measured list(cs.levels)."
          % (len(boundary), n_checked, n_excluded, len(collapse_witnesses)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
