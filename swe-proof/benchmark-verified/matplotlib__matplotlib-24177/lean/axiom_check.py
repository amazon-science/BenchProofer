#!/usr/bin/env python
"""G-AX: A-reference validation for matplotlib__matplotlib-24177.

Runs INSIDE the instance image (PYTHONPATH=/testbed). The bundle declares the
UNCHANGED callee `sampledVertices : List (Rat × Rat) → Bool → List (Rat × Rat)`
(opaque) modeling `Path.iter_bezier(simplify=…)` composed with the source's
per-segment endpoint extraction. The property the proof consumes is the
keep-all (`false` ↦ `simplify=False`) branch:

  for a polyline path, the keep-all sampled point set ranges over EXACTLY the
  path's defining points (every defining vertex appears among the collected
  points, and every collected point is one of the defining vertices).

This script runs the REAL callee `Path.iter_bezier(simplify=False)` on boundary
+ fuzzed polylines and asserts that property holds. It additionally demonstrates
the soundness of distinguishing the two branches: the may-drop branch
(`simplify=True`, the pre-patch configuration) can OMIT defining vertices — so
the keep-all guarantee is genuinely stronger and not vacuous.

stdlib + numpy + matplotlib only. Exit 0 iff the keep-all property holds on
every observation.
"""
import random
import sys

SEED = 20240630


def keepall_pointset(verts):
    """REAL callee: keep-all sampled points for a polyline Path(verts)."""
    import numpy as np
    from matplotlib.path import Path
    p = Path(np.asarray(verts, dtype=float))
    out = []
    for curve, code in p.iter_bezier(simplify=False):
        _, dzeros = curve.axis_aligned_extrema()
        pts = curve(np.concatenate([[0], dzeros, [1]]))
        for row in np.atleast_2d(pts):
            out.append((round(float(row[0]), 6), round(float(row[1]), 6)))
    return out


def main():
    import numpy as np

    rng = random.Random(SEED)
    violations = 0
    checked = 0
    drop_witnessed = 0

    def rand_polyline(n):
        return [(round(rng.uniform(-50, 50), 2), round(rng.uniform(-50, 50), 2))
                for _ in range(n)]

    cases = []
    # boundary cases
    cases.append([(0.0, 0.0), (1.0, 1.0)])
    cases.append([(-5.45, 0.0), (0.0, 0.33), (4.93, 0.0)])
    cases.append([(0.0, 0.0), (0.0, 0.0), (1.0, 0.0)])  # duplicate vertex
    for n in (2, 3, 4, 8, 32, 100, 130):
        cases.append(rand_polyline(n))
    for _ in range(2000):
        cases.append(rand_polyline(rng.randint(2, 16)))

    for verts in cases:
        defining = set((round(x, 6), round(y, 6)) for (x, y) in verts)
        collected = set(keepall_pointset(verts))
        checked += 1
        # keep-all property: defining points ⊆ collected, and collected ⊆ defining
        # (a polyline's order-≤1 segments contribute only their endpoints).
        if not defining.issubset(collected):
            violations += 1
            if violations <= 5:
                missing = defining - collected
                print(f"VIOLATION keep-all dropped {list(missing)[:3]} "
                      f"for verts (n={len(verts)})")
        if not collected.issubset(defining):
            violations += 1
            if violations <= 5:
                extra = collected - defining
                print(f"VIOLATION keep-all invented {list(extra)[:3]} "
                      f"for verts (n={len(verts)})")

        # soundness witness: the may-drop config CAN omit defining vertices,
        # confirming the keep-all guarantee is non-vacuous (not asserted, logged).
        from matplotlib.path import Path
        p = Path(np.asarray(verts, dtype=float))
        try:
            ms = set()
            for curve, code in p.iter_bezier(simplify=True):
                _, dz = curve.axis_aligned_extrema()
                pts = curve(np.concatenate([[0], dz, [1]]))
                for row in np.atleast_2d(pts):
                    ms.add((round(float(row[0]), 6), round(float(row[1]), 6)))
            if not defining.issubset(ms):
                drop_witnessed += 1
        except Exception:
            pass

    print(f"checked={checked} violations={violations} "
          f"may_drop_witnessed={drop_witnessed}")
    if violations == 0:
        print(f"status=pass keep-all ranges over exactly the defining points "
              f"({checked} observations, 0 violations)")
        return 0
    print(f"status=fail {violations} keep-all violation(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
