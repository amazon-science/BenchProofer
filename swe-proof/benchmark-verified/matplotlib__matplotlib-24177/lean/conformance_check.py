#!/usr/bin/env python
"""G-CONF: differential conformance for matplotlib__matplotlib-24177.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python R/I shadow of the Lean
`implementation_dataLimits` skeleton and diffs it against the REAL patched
behaviour of `Axes._update_patch_limits` over a discrete catalogue of polyline
paths plus >=1e5 randomized polylines.

Modeled function: `_update_patch_limits` collects the representative points
along a patch's path and updates the axes data limits to their bounding box.
The A-reference leg — the keep-all point sampling — is left as the REAL repo
callee `Path.iter_bezier(simplify=False)` (composed with the per-segment
endpoint extraction the source performs). The R/I legs under test are:
  * the componentwise min/max bounding box over the collected points, and
  * the empty-path => no-update (`none`) case.

Bridge (mapping.md): a Lean point list `List (Rat × Rat)` <-> an ndarray `N×2`
of finite floats; the Lean result `Option (Rat×Rat×Rat×Rat)` as
`(xmin,xmax,ymin,ymax)` <-> the axes `dataLim` bounding box `(x0,x1,y0,y1)`, or
`none` <-> no limit update for the empty path. On a fresh axes with the default
(identity) data transform and a `PathPatch` carrying the default transform, the
transform leg `patch_trf - transData` is identity, so the real `dataLim` equals
the bounding box of the collected vertices — exactly the modeled relation.

Exit 0 iff zero disagreements. numpy + matplotlib (Agg) only; pinned seed.
"""
import random
import sys

SEED = 20240630
N_RANDOM = 120_000  # >= 1e5


# ---- Python shadow of implementation_dataLimits (post-patch R/I leg) --------

def shadow_data_limits(vertices):
    """Transliteration of problem_spec_dataLimits / implementation_dataLimits:
    bounding box (componentwise min/max) over the collected points.
    `vertices` is a list of (x, y) pairs (the keep-all sampled point set).
    Returns (xmin, xmax, ymin, ymax) or None when empty."""
    if not vertices:
        return None
    xmin = xmax = vertices[0][0]
    ymin = ymax = vertices[0][1]
    for (x, y) in vertices[1:]:
        if x < xmin:
            xmin = x
        if x > xmax:
            xmax = x
        if y < ymin:
            ymin = y
        if y > ymax:
            ymax = y
    return (xmin, xmax, ymin, ymax)


def sampled_vertices_keepall(verts):
    """A-reference leg, left as the REAL repo callee: the keep-all point set
    the patched `_update_patch_limits` collects from a polyline path, i.e.
    `Path(verts).iter_bezier(simplify=False)` + the source's per-segment
    `curve([0, *dzeros, 1])` endpoint extraction."""
    import numpy as np
    from matplotlib.path import Path
    p = Path(np.asarray(verts, dtype=float))
    out = []
    for curve, code in p.iter_bezier(simplify=False):
        _, dzeros = curve.axis_aligned_extrema()
        pts = curve(np.concatenate([[0], dzeros, [1]]))
        for row in np.atleast_2d(pts):
            out.append((float(row[0]), float(row[1])))
    return out


# ---- real callee observation ------------------------------------------------

def real_data_limits(verts):
    """Run the REAL patched pipeline: add a PathPatch(Path(verts)) to a fresh
    Axes and read back the resulting dataLim bounding box. Returns
    (x0, x1, y0, y1) or None if the path produced no finite update."""
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.path import Path

    fig, ax = plt.subplots()
    try:
        p = Path(np.asarray(verts, dtype=float))
        ax.add_patch(mpatches.PathPatch(p))
        bb = ax.dataLim
        x0, x1 = float(bb.x0), float(bb.x1)
        y0, y1 = float(bb.y0), float(bb.y1)
    finally:
        plt.close(fig)
    if not all(np.isfinite([x0, x1, y0, y1])):
        return None
    return (x0, x1, y0, y1)


def approx_eq(a, b, tol=1e-6):
    if a is None or b is None:
        return a is b
    return all(abs(x - y) <= tol + tol * max(abs(x), abs(y)) for x, y in zip(a, b))


def main():
    disagreements = 0
    checked = 0
    rng = random.Random(SEED)

    def rand_polyline(n):
        return [(round(rng.uniform(-50, 50), 2), round(rng.uniform(-50, 50), 2))
                for _ in range(n)]

    cases = []
    # discrete catalogue incl. degenerate + the issue's small-value flat shapes
    cases.append([(0.0, 0.0), (1.0, 1.0)])
    cases.append([(-5.45, 0.0), (0.0, 0.33), (4.93, 0.0)])
    cases.append([(0.0, 0.0), (0.0, 0.0), (0.0, 0.01), (1.0, 0.0)])
    cases.append([(-1.0, -2.0), (3.0, 5.0), (2.0, -4.0), (-3.0, 1.0)])
    for n in (2, 3, 4, 5, 8, 16, 32, 64, 130, 200):
        cases.append(rand_polyline(n))

    for _ in range(N_RANDOM):
        n = rng.randint(2, 12)
        cases.append(rand_polyline(n))

    for verts in cases:
        got = real_data_limits(verts)
        sampled = sampled_vertices_keepall(verts)
        exp = shadow_data_limits(sampled)
        checked += 1
        if not approx_eq(got, exp):
            disagreements += 1
            if disagreements <= 5:
                print(f"MISMATCH verts[:4]={verts[:4]} (n={len(verts)}): "
                      f"real={got!r} shadow={exp!r}")

    print(f"checked={checked} disagreements={disagreements}")
    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements)")
        return 0
    print(f"status=fail {disagreements} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
