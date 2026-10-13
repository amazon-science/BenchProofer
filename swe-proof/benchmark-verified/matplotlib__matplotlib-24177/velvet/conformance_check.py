#!/usr/bin/env python3
r"""G-CONF differential conformance check for matplotlib__matplotlib-24177 (plan §4.1).

Runs IN-CONTAINER with the gold patch applied (the orchestrator passes
apply_gold=True), so the ORACLE is the patched repo's real behaviour.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing the OBSERVABLE the F2P test
checks — the data extent (the autoscale bounding box) a patch contributes to an
Axes via `Axes._update_patch_limits`.

  * ORACLE  — `patch.diff`'s behaviour: a real `PathPatch` (drawn in data
              coordinates) fed to the patched `Axes._update_patch_limits`, after
              which `ax.dataLim` holds the contributed extent. The whole patched
              method runs: the changed segment traversal AND all the unchanged
              upstream/downstream (`iter_bezier`, `axis_aligned_extrema`, the
              per-segment evaluation, `np.row_stack`, the transform, and
              `update_datalim`) are executed by the real patched repo.

  * SHADOW  — `Solution.lean`'s modeled operation (`collectVertices` + the pure
              `collectAll` concatenation) transliterated to Python over the real
              repo types, via the mapping.md §2 bijection:
                  segs : List (List Vertex)   <->  the per-segment point arrays
                       [curve([0, *dzeros, 1]) for curve, code in
                        path.iter_bezier(simplify=False)]
                  collectAll segs             <->  np.row_stack(segs) (the
                       in-order concatenation of all segments' point lists)
              The per-segment point arrays are produced by the SAME real
              unchanged upstream (`iter_bezier(simplify=False)` +
              `axis_aligned_extrema` + the curve evaluation) the patched code
              uses — the I-reference, run via the real repo, not re-modeled. The
              collected points are then carried to the SAME unchanged downstream
              extent (min/max over the points = the data bounding box the
              patched `update_datalim` produces under the identity data
              transform). There are NO A-tagged ops (no consumed axioms, no
              deep-model references): the modeled fold is pure R/I (conf_skip=
              false), and `segs` is an INPUT supplied by the unchanged upstream.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

stdlib + numpy + matplotlib (Agg, no display). Fuzz seed pinned (mapping.md §4).
"""
import random
import sys

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import PathPatch

SEED = 24177
N_FUZZ = 100_000

# vertices consumed per Path code (a multi-vertex code repeats over its rows).
_NUM_VERTS = {Path.MOVETO: 1, Path.LINETO: 1, Path.CURVE3: 2, Path.CURVE4: 3}


# --- SHADOW: the R/I transliteration of collectAll / collectVertices ---------

def shadow_extent(path):
    """np.row_stack(collectAll segs) -> bbox, where `segs` is the per-segment
    point lists from the real unchanged upstream `iter_bezier(simplify=False)`.
    This is the modeled concatenation fold, carried to the unchanged downstream
    extent under the identity data transform."""
    segs = []                                       # segs : List (List Vertex)
    for curve, code in path.iter_bezier(simplify=False):   # unchanged upstream
        _, dzeros = curve.axis_aligned_extrema()
        segs.append(curve([0, *dzeros, 1]))         # this segment's point list
    if not segs:                                    # collectAll [] = []
        return None
    verts = np.row_stack(segs)                       # collectAll = concatenation
    return (verts[:, 0].min(), verts[:, 1].min(),
            verts[:, 0].max(), verts[:, 1].max())


# --- ORACLE: the real patched Axes._update_patch_limits ----------------------

def oracle_extent(path):
    """patch.diff's behaviour: feed a data-coordinate PathPatch to the patched
    _update_patch_limits, then read the contributed data extent."""
    fig, ax = plt.subplots()
    try:
        patch = PathPatch(path, transform=ax.transData)
        ax._update_patch_limits(patch)
        pts = ax.dataLim.get_points()
        return (pts[0, 0], pts[0, 1], pts[1, 0], pts[1, 1])
    finally:
        plt.close(fig)


# --- fuzz: random open/closed paths of lines and Bezier curves ---------------

def _rand_path(rng):
    seq = [Path.MOVETO]
    n = rng.randint(1, 6)
    for _ in range(n):
        seq.append(rng.choice([Path.LINETO, Path.CURVE3, Path.CURVE4]))
    close = rng.random() < 0.3
    verts, codes = [], []
    for c in seq:
        for _ in range(_NUM_VERTS[c]):
            verts.append([rng.uniform(-5.0, 5.0), rng.uniform(-0.01, 0.5)])
            codes.append(c)
    if close:
        verts.append([0.0, 0.0])
        codes.append(Path.CLOSEPOLY)
    return Path(np.array(verts, float), codes)


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4)
    # the issue's signature: a long, nearly-flat small-valued outline whose
    # interior bump would be dropped by a reducing traversal.
    xs = np.linspace(-5.45, 5.45, 70)
    ys = (np.abs(xs) < 3.3).astype(float) * 0.33 * (1 - (xs / 3.3) ** 2).clip(0)
    verts = np.column_stack([xs, ys])
    yield Path(verts, [Path.MOVETO] + [Path.LINETO] * (len(xs) - 1))
    # a single line, a single point, a triangle, one cubic curve
    yield Path(np.array([[-5.0, 0.0], [5.0, 0.0]]), [Path.MOVETO, Path.LINETO])
    yield Path(np.array([[1.0, 2.0]]), [Path.MOVETO])
    yield Path(np.array([[-1.0, 0.0], [0.0, 0.4], [1.0, 0.0], [0.0, 0.0]]),
               [Path.MOVETO, Path.LINETO, Path.LINETO, Path.CLOSEPOLY])
    yield Path(np.array([[-2.0, 0.0], [-1.0, 1.0], [1.0, -1.0], [2.0, 0.0]]),
               [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4])
    for _ in range(n):
        yield _rand_path(rng)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for path in fuzz_inputs(N_FUZZ, rng):
        try:
            oracle = oracle_extent(path)
        except Exception:
            continue
        shadow = shadow_extent(path)
        count += 1
        if shadow is None:
            # collectAll [] = [] (no Bezier segments): the patched method makes
            # no extent contribution either; nothing to compare.
            continue
        if not np.allclose(np.array(shadow, float), np.array(oracle, float),
                           atol=1e-9, rtol=1e-12, equal_nan=True):
            disagreements.append((shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for sh, orc in disagreements:
            print("  shadow=%r oracle=%r" % (sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of collectVertices (np.row_stack of all "
          "iter_bezier(simplify=False) segments) agrees with patch.diff "
          "behaviour (real Axes._update_patch_limits data extent) on %d inputs "
          "(seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
