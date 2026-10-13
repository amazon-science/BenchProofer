#!/usr/bin/env python
"""G-CONF: differential conformance for matplotlib__matplotlib-25960.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python shadow of the Lean
`implementation_subfigureGrid` / `gridRects` skeleton and diffs it against the
REAL patched `Figure.subfigures` over a discrete catalogue plus >=1e5 randomized
draws.

  observable: for a figure with no layout engine, calling
  `subfigures(nrows, ncols, wspace=ws, hspace=hs)` and reading each returned
  subfigure's relative bounding box `(x0, y0, x1, y1)` in figure-fraction
  coordinates. We recover the relative box from the pixel bbox:
    x0 = sf.bbox.min[0] / W,  y0 = sf.bbox.min[1] / H,
    x1 = sf.bbox.max[0] / W,  y1 = sf.bbox.max[1] / H   (W,H = figure px size)

The shadow returns gridRects(nrows, ncols, ws, hs) as exact Fractions. Both legs
are compared with an absolute tolerance (float vs exact rational). Exit 0 iff
zero disagreements. stdlib-only fuzzing (pinned seed); only matplotlib + Fraction.
"""
import random
import sys
from fractions import Fraction as F

SEED = 20250630
N_RANDOM = 120_000  # >= 1e5
TOL = 1e-9


# ---- Python shadow of implementation_subfigureGrid / gridRects --------------

def panel_extent(k, s):
    # 1 / (k + s*(k-1))
    return F(1, 1) / (F(k) + s * (F(k) - 1))


def panel_gap(k, s):
    return s * panel_extent(k, s)


def grid_rects(nrows, ncols, ws, hs):
    cw = panel_extent(ncols, ws)
    sw = panel_gap(ncols, ws)
    ch = panel_extent(nrows, hs)
    sh = panel_gap(nrows, hs)
    out = []
    for j in range(nrows):
        top = F(1) - j * (ch + sh)
        bottom = top - ch
        row = []
        for i in range(ncols):
            left = i * (cw + sw)
            right = left + cw
            row.append((left, bottom, right, top))  # x0,y0,x1,y1
        out.append(row)
    return out


# ---- real callee observation ------------------------------------------------

def real_rects(nrows, ncols, ws, hs):
    """Run the REAL patched subfigures (no layout engine) and return each
    subfigure's relative bbox (x0,y0,x1,y1)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig = plt.figure()
    try:
        W, H = fig.bbox.max  # pixel size
        sfs = fig.subfigures(nrows, ncols, squeeze=False,
                             wspace=ws, hspace=hs)
        out = []
        for j in range(nrows):
            row = []
            for i in range(ncols):
                sf = sfs[j, i]
                x0, y0 = sf.bbox.min
                x1, y1 = sf.bbox.max
                row.append((x0 / W, y0 / H, x1 / W, y1 / H))
            out.append(row)
    finally:
        plt.close(fig)
    return out


def main():
    disagreements = 0
    checked = 0

    def close(a, b):
        return abs(float(a) - float(b)) <= TOL

    def check(nrows, ncols, ws, hs):
        nonlocal disagreements, checked
        got = real_rects(nrows, ncols, ws, hs)
        exp = grid_rects(nrows, ncols, F(ws).limit_denominator(10**9), F(hs).limit_denominator(10**9))
        checked += 1
        ok = True
        for j in range(nrows):
            for i in range(ncols):
                for g, e in zip(got[j][i], exp[j][i]):
                    if not close(g, e):
                        ok = False
        if not ok:
            disagreements += 1
            if disagreements <= 5:
                print(f"MISMATCH nrows={nrows} ncols={ncols} ws={ws} hs={hs}: "
                      f"real={got!r} shadow={[[tuple(float(v) for v in r) for r in row] for row in exp]!r}")

    # ---- discrete catalogue (incl. the F2P configuration) ----
    discrete = [
        (2, 3, 1 / 6, 0.5),    # the F2P test
        (2, 2, 0.0, 0.0),
        (2, 2, 0.2, 0.2),
        (1, 3, 0.5, 0.0),
        (3, 1, 0.0, 0.5),
        (1, 1, 0.0, 0.0),
        (4, 2, 0.1, 0.3),
        (2, 4, 0.25, 0.25),
        (3, 3, 1.0, 1.0),
    ]
    for (r, c, ws, hs) in discrete:
        check(r, c, ws, hs)

    # ---- randomized fuzz ----
    rng = random.Random(SEED)
    for _ in range(N_RANDOM):
        nrows = rng.randint(1, 5)
        ncols = rng.randint(1, 5)
        # spacing as simple rationals to keep the float<->Fraction bridge exact-ish
        ws = rng.choice([0, 0.1, 0.2, 0.25, 0.5, 1 / 6, 0.75, 1.0, 2.0])
        hs = rng.choice([0, 0.1, 0.2, 0.25, 0.5, 1 / 3, 0.6, 1.0, 1.5])
        check(nrows, ncols, ws, hs)

    print(f"checked={checked} disagreements={disagreements}")
    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements)")
        return 0
    print(f"status=fail {disagreements} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
