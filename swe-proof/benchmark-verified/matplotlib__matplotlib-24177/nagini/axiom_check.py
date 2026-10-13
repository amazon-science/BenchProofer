#!/usr/bin/env python3
"""G-AX executable soundness check for matplotlib__matplotlib-24177.

Executes the REAL callee the gathering routine invokes -- `matplotlib.path.
Path.iter_bezier` (and, through it, the path-condensation in `Path.cleaned` /
`_path.cleanup_path`) -- on a battery of paths (boundary outlines plus
randomized fuzz, including the exact regression outline from the issue) and
asserts that every observation matches what model.py relies on.

Two kind-A obligations (model.py axioms + deep model):

  (A-consumed) the `condensed_len` / `condensed_at` axioms model the
      appearance-preserving condensation of a path (`iter_bezier()` with the
      default `simplify=None`, i.e. simplification ENABLED for a long
      MOVETO/LINETO path). Their ONLY guaranteed property -- the weakest sound
      contract -- is MEMBERSHIP: every value the condensation emits already
      occurs among the path's own vertices, and the retained count never exceeds
      the full count. G-AX confirms membership for the condensed gather. It also
      witnesses, on the regression outline, that the condensation OMITS the
      vertex carrying the extreme coordinate -- i.e. the axiom rightly promises
      NOTHING about preserving the extremes (which is exactly why the pre-patch
      gather is unsound).

  (A-reference) the deep model `seq_max` over the FULL gather (`iter_bezier`
      with `simplify=False`) is validated: gathering every vertex yields an
      extent whose upper end is >= the largest coordinate of EVERY path vertex
      (and whose lower end is <= the smallest). This is the enclosing property
      `enclosing_upper_bound` proves and that the autoscaled view requires.

The gather mirrors `Axes._update_patch_limits`: for each (curve, code) from
`iter_bezier(...)`, the curve is sampled at [0, *extrema, 1] and those points
are collected. Imports `matplotlib.path` / `matplotlib.bezier` (the very modules
the gather uses) and `numpy`; nothing else repo-specific. Exit 0 iff sound.
"""
import random
import sys

import numpy as np
from matplotlib.path import Path


# --- the gather, exactly as Axes._update_patch_limits performs it ------------

def gather_vertices(path, simplify):
    """Reproduce the per-segment vertex gather of `_update_patch_limits` for a
    given `simplify` setting, returning the collected (x, y) points as an
    Nx2 array (empty array if the path yields nothing)."""
    collected = []
    for curve, code in path.iter_bezier(simplify=simplify):
        _, dzeros = curve.axis_aligned_extrema()
        collected.append(curve([0, *dzeros, 1]))
    if len(collected):
        return np.row_stack(collected)
    return np.empty((0, 2))


def axis_values(verts_nx2, axis):
    return [float(v) for v in verts_nx2[:, axis]]


# --- A-consumed: membership of the condensed gather --------------------------

def check_condensation_membership(path):
    """The condensation (simplify enabled) emits only values already present
    among the path's vertices, and never more values than the path has. This is
    the weakest sound contract the `condensed_*` axioms encode."""
    raw = path.vertices
    condensed = gather_vertices(path, simplify=None)  # None -> should_simplify
    full = gather_vertices(path, simplify=False)

    raw_count = raw.shape[0]
    # condensed_len <= len(verts): never invent vertices.
    assert condensed.shape[0] <= full.shape[0], (
        "condensed_len axiom unsound: condensation emitted MORE points (%d) "
        "than the full gather (%d)" % (condensed.shape[0], full.shape[0]))

    # condensed_at membership: every emitted value occurs among the path's
    # vertices (checked per axis, since the model carrier is one axis).
    for axis in (0, 1):
        present = set(round(float(x), 9) for x in raw[:, axis]) if raw_count else set()
        # the full gather of a MOVETO/LINETO path is exactly the path vertices
        present |= set(round(float(x), 9) for x in axis_values(full, axis))
        for x in axis_values(condensed, axis):
            assert round(x, 9) in present, (
                "condensed_at axiom unsound on axis %d: condensation emitted "
                "value %r that does not occur among the path vertices" % (axis, x))


# --- A-reference: the full gather encloses every vertex ----------------------

def check_full_gather_encloses(path):
    """With simplify=False the gather covers every path vertex, so the extent
    encloses the path: max(gathered) >= max(all vertices), min <= min. This is
    the deep `seq_max` enclosing property `enclosing_upper_bound` proves."""
    raw = path.vertices
    if raw.shape[0] == 0:
        return
    full = gather_vertices(path, simplify=False)
    assert full.shape[0] >= 1, "full gather lost all vertices"
    for axis in (0, 1):
        gathered = axis_values(full, axis)
        allv = [float(v) for v in raw[:, axis]]
        gmax, gmin = max(gathered), min(gathered)
        amax, amin = max(allv), min(allv)
        assert gmax >= amax - 1e-9, (
            "A-reference unsound on axis %d: full-gather max %r < path max %r"
            % (axis, gmax, amax))
        assert gmin <= amin + 1e-9, (
            "A-reference unsound on axis %d: full-gather min %r > path min %r"
            % (axis, gmin, amin))


# --- the regression outline from the issue (#24097) --------------------------

# The step-histogram outline from the F2P fixture (test_small_autoscale): 132
# MOVETO/LINETO vertices (>= 128 so the path's should_simplify is True), with the
# y-extreme on an interior vertex that the condensation drops. This is the EXACT
# vertex array the regression test plots; derive the witness from the F2P fixture
# (not a synthetic curve, which smooth-curve condensation may keep intact).
def regression_outline():
    verts = np.array([
        [-5.45, 0.00], [-5.45, 0.00], [-5.29, 0.00], [-5.29, 0.00],
        [-5.13, 0.00], [-5.13, 0.00], [-4.97, 0.00], [-4.97, 0.00],
        [-4.81, 0.00], [-4.81, 0.00], [-4.65, 0.00], [-4.65, 0.00],
        [-4.49, 0.00], [-4.49, 0.00], [-4.33, 0.00], [-4.33, 0.00],
        [-4.17, 0.00], [-4.17, 0.00], [-4.01, 0.00], [-4.01, 0.00],
        [-3.85, 0.00], [-3.85, 0.00], [-3.69, 0.00], [-3.69, 0.00],
        [-3.53, 0.00], [-3.53, 0.00], [-3.37, 0.00], [-3.37, 0.00],
        [-3.21, 0.00], [-3.21, 0.01], [-3.05, 0.01], [-3.05, 0.01],
        [-2.89, 0.01], [-2.89, 0.01], [-2.73, 0.01], [-2.73, 0.02],
        [-2.57, 0.02], [-2.57, 0.04], [-2.41, 0.04], [-2.41, 0.04],
        [-2.25, 0.04], [-2.25, 0.06], [-2.09, 0.06], [-2.09, 0.08],
        [-1.93, 0.08], [-1.93, 0.10], [-1.77, 0.10], [-1.77, 0.12],
        [-1.61, 0.12], [-1.61, 0.14], [-1.45, 0.14], [-1.45, 0.17],
        [-1.30, 0.17], [-1.30, 0.19], [-1.14, 0.19], [-1.14, 0.22],
        [-0.98, 0.22], [-0.98, 0.25], [-0.82, 0.25], [-0.82, 0.27],
        [-0.66, 0.27], [-0.66, 0.29], [-0.50, 0.29], [-0.50, 0.30],
        [-0.34, 0.30], [-0.34, 0.32], [-0.18, 0.32], [-0.18, 0.33],
        [-0.02, 0.33], [-0.02, 0.32], [0.13, 0.32], [0.13, 0.33],
        [0.29, 0.33], [0.29, 0.31], [0.45, 0.31], [0.45, 0.30],
        [0.61, 0.30], [0.61, 0.28], [0.77, 0.28], [0.77, 0.25],
        [0.93, 0.25], [0.93, 0.22], [1.09, 0.22], [1.09, 0.19],
        [1.25, 0.19], [1.25, 0.17], [1.41, 0.17], [1.41, 0.15],
        [1.57, 0.15], [1.57, 0.12], [1.73, 0.12], [1.73, 0.10],
        [1.89, 0.10], [1.89, 0.08], [2.05, 0.08], [2.05, 0.07],
        [2.21, 0.07], [2.21, 0.05], [2.37, 0.05], [2.37, 0.04],
        [2.53, 0.04], [2.53, 0.02], [2.69, 0.02], [2.69, 0.02],
        [2.85, 0.02], [2.85, 0.01], [3.01, 0.01], [3.01, 0.01],
        [3.17, 0.01], [3.17, 0.00], [3.33, 0.00], [3.33, 0.00],
        [3.49, 0.00], [3.49, 0.00], [3.65, 0.00], [3.65, 0.00],
        [3.81, 0.00], [3.81, 0.00], [3.97, 0.00], [3.97, 0.00],
        [4.13, 0.00], [4.13, 0.00], [4.29, 0.00], [4.29, 0.00],
        [4.45, 0.00], [4.45, 0.00], [4.61, 0.00], [4.61, 0.00],
        [4.77, 0.00], [4.77, 0.00], [4.93, 0.00], [4.93, 0.00],
    ])
    return Path(verts)


def check_regression_witness():
    """On the regression outline the CONDENSED gather misses the y-extreme
    (its max is strictly below the true max), while the FULL gather captures it.
    This is the discriminator: the condensation axiom rightly promises nothing
    about the extremes, so the pre-patch gather (condensed) cannot enclose the
    path, whereas the patched gather (full) does."""
    path = regression_outline()
    raw = path.vertices
    true_ymax = max(float(v) for v in raw[:, 1])

    full = gather_vertices(path, simplify=False)
    cond = gather_vertices(path, simplify=None)
    full_ymax = max(axis_values(full, 1))
    cond_ymax = max(axis_values(cond, 1)) if cond.shape[0] else float("-inf")

    assert abs(full_ymax - true_ymax) <= 1e-9, (
        "full gather should capture the true y-extreme %r, got %r"
        % (true_ymax, full_ymax))
    # The whole point of the bug: the condensed gather UNDERSHOOTS the extreme.
    assert cond_ymax < true_ymax - 1e-6, (
        "expected the condensation to DROP the y-extreme on the regression "
        "outline (cond max %r should be < true max %r); if this fails the "
        "installed matplotlib does not simplify this path -- adjust the witness"
        % (cond_ymax, true_ymax))
    # And it still satisfies membership (the axiom IS sound, just weak).
    check_condensation_membership(path)
    check_full_gather_encloses(path)


# --- fuzz outlines -----------------------------------------------------------

def random_step_outline(rng):
    n = rng.randint(2, 90)
    verts = []
    x = rng.uniform(-10, 10)
    for _ in range(n):
        x += rng.uniform(0.05, 0.4)
        y = rng.uniform(0.0, 5.0)
        verts.append([x, 0.0])
        verts.append([x, y])
    return Path(np.array(verts))


def main():
    # --- boundary outlines -------------------------------------------------
    boundary = [
        Path(np.array([[0.0, 0.0], [1.0, 1.0]])),            # single segment
        Path(np.array([[0.0, 0.0], [1.0, 2.0], [2.0, 0.0]])),
        Path(np.array([[0.0, 0.0]])),                        # single point
        regression_outline(),
    ]
    for path in boundary:
        check_condensation_membership(path)
        check_full_gather_encloses(path)

    # the load-bearing discriminator from the issue
    check_regression_witness()

    # --- randomized fuzz ---------------------------------------------------
    rng = random.Random(24177)
    for _ in range(4000):
        path = random_step_outline(rng)
        check_condensation_membership(path)
        check_full_gather_encloses(path)

    print("G-AX OK: condensation membership (condensed_len/condensed_at weakest "
          "sound contract) verified; full-gather (simplify=False) encloses every "
          "vertex (deep seq_max A-reference); regression-outline witness shows "
          "the condensation drops the interior y-extreme over 4 boundary + 4000 "
          "fuzz outlines.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
