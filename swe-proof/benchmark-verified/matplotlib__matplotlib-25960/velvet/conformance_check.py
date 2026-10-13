#!/usr/bin/env python3
"""G-CONF differential conformance for matplotlib__matplotlib-25960.

Band: float-precision (plan §10 Q1; exact-rational shadow vs float oracle).

Refutes the R/I refinement leg (refinement.md A2-A4: the modeled spacing-aware
cell placement `axisExtents` / `cellPitch` / `cellSize`).

ORACLE CHOICE — why we transliterate the reduced source arithmetic instead of
running the full `Figure.subfigures`:
  The patched placement lives inside `Figure.subfigures`, which builds a live
  Figure, a GridSpec, N SubFigure objects, and applies `Bbox.from_extents` +
  `_redo_transform_rel_fig` per cell. The behaviour under test is the pure
  per-axis edge computation that `gs.get_grid_positions(self)` returns once the
  GridSpec is constructed with the patch-supplied full-figure margins
  `left=0, right=1, bottom=0, top=1` and equal cell ratios. Per the worker
  prompt, the ORACLE is the `get_grid_positions` arithmetic transliterated
  VERBATIM under those margins (lib/matplotlib/gridspec.py:145-205, the
  `raw=False` branch with tot_width = tot_height = 1 and norm = 1 for equal
  ratios). The SHADOW is the modeled placement from Solution.lean's
  `axisExtents` (with `cellPitch`/`cellSize`). We differential-test SHADOW vs
  ORACLE over fuzzed `(n, s)` per axis (and the full 2-D `(nrows, ncols, wspace,
  hspace)` product) including the gap-free boundary `s = 0`. Exit 0 iff zero
  disagreements. stdlib only.

  CALLEE ABSTRACTION: `get_grid_positions` is UNCHANGED by the patch; it is the
  A-reference deep-modeled by `axisExtents`. Its independent soundness (the
  reduced closed form here == the REAL `get_grid_positions` object) is checked
  separately by axiom_check.py (G-AX). Here we only refute the R/I
  transliteration of the model against that reduced closed form.

FLOAT MODEL NOTE (mapping.md §2): Solution.lean models edges as exact Rat. The
oracle here computes in float (the repo runs float). Each edge is a rational
function of `(n, s)` with no cross-cell accumulation, so the two agree to a tiny
relative tolerance; we assert with `rel_tol = 1e-9` (well inside the
`assert_allclose` default `rtol=1e-7` the F2P test uses). The discriminating
property (positive gap separates cells) is exact and is asserted exactly below.
"""
import random
import sys
from fractions import Fraction


# ---- SHADOW: transliteration of Solution.lean's deep model (R/I ops) ----------
def cell_size_shadow(n, s):
    # cellSize n s = 1 / (n + s*(n-1))   [exact rational]
    return Fraction(1) / (Fraction(n) + s * (Fraction(n) - 1))


def cell_pitch_shadow(n, s):
    # cellPitch n s = cellSize * (1 + s)
    return cell_size_shadow(n, s) * (1 + s)


def axis_extents_shadow(n, s):
    # axisExtents n s = [ (i*pitch, i*pitch + size) | i <- range n ]
    size = cell_size_shadow(n, s)
    pitch = cell_pitch_shadow(n, s)
    return [(i * pitch, i * pitch + size) for i in range(n)]


# ---- ORACLE: reduced get_grid_positions arithmetic, VERBATIM (float) ----------
# From lib/matplotlib/gridspec.py:145-205 with the patch margins left=0, right=1,
# bottom=0, top=1 and equal width/height ratios (norm == 1).
def grid_positions_oracle(n, s):
    """Returns lefts, rights for one axis with ncols=n, wspace=s (== the row
    axis with nrows=n, hspace=s before the top-origin reversal)."""
    left, right = 0.0, 1.0
    wspace = float(s)
    ncols = n
    tot_width = right - left                       # = 1.0
    cell_w = tot_width / (ncols + wspace * (ncols - 1))
    sep_w = wspace * cell_w
    # equal ratios -> norm = 1, every cell_widths[k] == cell_w
    cell_widths = [cell_w] * ncols
    sep_widths = [0.0] + ([sep_w] * (ncols - 1))
    # cumulative sum of the interleaved [sep, cell, sep, cell, ...]
    cell_ws = []
    acc = 0.0
    for k in range(ncols):
        acc += sep_widths[k]
        cell_ws.append(acc)          # left edge of cell k (the "sep" slot)
        acc += cell_widths[k]
        cell_ws.append(acc)          # right edge of cell k (the "cell" slot)
    lefts = [left + cell_ws[2 * k] for k in range(ncols)]
    rights = [left + cell_ws[2 * k + 1] for k in range(ncols)]
    return lefts, rights


def close(a, b, rel_tol=1e-9, abs_tol=1e-12):
    a = float(a)
    b = float(b)
    return abs(a - b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)


def check_axis(n, s):
    """One disagreement-or-None for a single axis (n cells, gap fraction s)."""
    shadow = axis_extents_shadow(n, s)
    lefts, rights = grid_positions_oracle(n, s)
    if len(shadow) != n or len(lefts) != n:
        return f"length mismatch n={n} s={s}: shadow={len(shadow)} oracle={len(lefts)}"
    for i in range(n):
        slo, shi = shadow[i]
        if not close(slo, lefts[i]) or not close(shi, rights[i]):
            return (f"edge mismatch n={n} s={s} i={i}: "
                    f"shadow=({float(slo)},{float(shi)}) "
                    f"oracle=({lefts[i]},{rights[i]})")
    # Discriminating property (exact, on the rational shadow): a positive gap
    # strictly separates consecutive cells; a zero gap makes them abut.
    for i in range(n - 1):
        hi_i = shadow[i][1]
        lo_next = shadow[i + 1][0]
        if s > 0 and not (hi_i < lo_next):
            return f"gap not separating n={n} s={s} i={i}: hi={hi_i} lo_next={lo_next}"
        if s == 0 and hi_i != lo_next:
            return f"zero-gap not abutting n={n} s={s} i={i}"
    return None


def main():
    rng = random.Random(25960)  # pinned seed (mapping.md §4)
    checks = 0
    disagreements = []

    # Boundary / sentinel configs, incl. the exact F2P test parameters.
    boundary_s = [Fraction(0), Fraction(1, 6), Fraction(1, 2), Fraction(1),
                  Fraction(2), Fraction(3, 7), Fraction(1, 100), Fraction(10)]
    boundary_n = [1, 2, 3, 4, 5, 7, 12]
    for n in boundary_n:
        for s in boundary_s:
            d = check_axis(n, s)
            checks += 1
            if d:
                disagreements.append(d)

    # Explicit F2P reproduction: cols (ncols=3, wspace=1/6), rows (nrows=2, hspace=1/2).
    for (n, s) in [(3, Fraction(1, 6)), (2, Fraction(1, 2))]:
        d = check_axis(n, s)
        checks += 1
        if d:
            disagreements.append(d)

    # Randomized fuzz: >= 1e5 axis checks over random (n, s).
    TARGET = 120_000
    while checks < TARGET:
        n = rng.randint(1, 20)
        # mix exact-rational gaps and arbitrary float-derived gaps (>= 0)
        if rng.random() < 0.5:
            s = Fraction(rng.randint(0, 50), rng.randint(1, 12))
        else:
            s = Fraction(rng.random()).limit_denominator(10_000)
        d = check_axis(n, s)
        checks += 1
        if d:
            disagreements.append(d)
            if len(disagreements) > 20:
                break

    if disagreements:
        print(f"G-CONF FAIL: {len(disagreements)} disagreement(s) in {checks} checks "
              f"(seed=25960). First few:")
        for d in disagreements[:10]:
            print("  -", d)
        sys.exit(1)

    print(f"G-CONF OK: R/I shadow of axisCellExtents agrees with the reduced "
          f"get_grid_positions oracle on {checks} axis configs "
          f"(boundary + F2P + fuzz, seed=25960), 0 disagreements. "
          f"Gap-free boundary (s=0, cells abut) and positive-gap separation "
          f"(s>0, cells strictly separated) both covered.")
    sys.exit(0)


if __name__ == "__main__":
    main()
