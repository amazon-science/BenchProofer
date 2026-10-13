#!/usr/bin/env python3
"""G-AX soundness check for matplotlib__matplotlib-25960.

Validates the ONE deep-model reference (A-reference) of the bundle:

    Solution.lean `axisExtents n s`  ==  the REAL
    matplotlib.gridspec.GridSpec.get_grid_positions(fig)

evaluated under the patch-supplied full-figure margins (left=0, right=1,
bottom=0, top=1) and equal cell ratios — exactly the configuration the patched
`Figure.subfigures` constructs. There is NO consumed axiom in this bundle, so
this script's sole job is to confirm the deep model equals the real callee on
boundary + fuzz inputs.

Correspondence checked (mapping.md §2, §3.1):
  - column axis:  lefts, rights  == axisExtents(ncols, wspace)
  - row    axis:  bottoms, tops  == reverse(axisExtents(nrows, hspace))
                  (get_grid_positions indexes rows from the top: top - cell_hs)

Runs the REAL get_grid_positions (imports only matplotlib). Exit 0 iff every
observation matches the model to a tight float tolerance.
"""
import sys
from fractions import Fraction

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec


# ---- the deep model from Solution.lean (exact rational) -----------------------
def cell_size(n, s):
    return Fraction(1) / (Fraction(n) + s * (Fraction(n) - 1))


def cell_pitch(n, s):
    return cell_size(n, s) * (1 + s)


def axis_extents(n, s):
    size = cell_size(n, s)
    pitch = cell_pitch(n, s)
    return [(i * pitch, i * pitch + size) for i in range(n)]


def close(a, b, rel_tol=1e-9, abs_tol=1e-12):
    a, b = float(a), float(b)
    return abs(a - b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)


def check_config(nrows, ncols, hspace, wspace):
    """Construct the REAL GridSpec exactly as the patched subfigures does and
    compare get_grid_positions against the model. Returns an error str or None."""
    fig = plt.figure()
    try:
        gs = GridSpec(nrows=nrows, ncols=ncols, figure=fig,
                      wspace=float(wspace), hspace=float(hspace),
                      left=0, right=1, bottom=0, top=1)
        bottoms, tops, lefts, rights = gs.get_grid_positions(fig)
    finally:
        plt.close(fig)

    # Column axis: lefts/rights == axisExtents(ncols, wspace), in column order.
    col_model = axis_extents(ncols, Fraction(wspace))
    for i in range(ncols):
        lo, hi = col_model[i]
        if not close(lo, lefts[i]) or not close(hi, rights[i]):
            return (f"col mismatch nrows={nrows} ncols={ncols} wspace={wspace} "
                    f"i={i}: model=({float(lo)},{float(hi)}) "
                    f"real=({lefts[i]},{rights[i]})")

    # Row axis: bottoms/tops == reverse(axisExtents(nrows, hspace)).
    # get_grid_positions returns rows top-first (top - cell_hs); with top=1 this
    # is the bottom-origin extents reversed.
    row_model = list(reversed(axis_extents(nrows, Fraction(hspace))))
    for j in range(nrows):
        lo, hi = row_model[j]
        if not close(lo, bottoms[j]) or not close(hi, tops[j]):
            return (f"row mismatch nrows={nrows} ncols={ncols} hspace={hspace} "
                    f"j={j}: model=({float(lo)},{float(hi)}) "
                    f"real=({bottoms[j]},{tops[j]})")
    return None


def main():
    import random
    rng = random.Random(25960)
    errors = []
    checks = 0

    # Boundary configs incl. the exact F2P parameters (nrows=2, ncols=3,
    # hspace=0.5, wspace=1/6) and the gap-free boundary (0).
    spaces = [Fraction(0), Fraction(1, 6), Fraction(1, 2), Fraction(1),
              Fraction(2), Fraction(1, 100)]
    sizes = [1, 2, 3, 4, 5, 7]
    for nrows in sizes:
        for ncols in sizes:
            for hspace in spaces:
                for wspace in spaces:
                    e = check_config(nrows, ncols, hspace, wspace)
                    checks += 1
                    if e:
                        errors.append(e)

    # Explicit F2P reproduction.
    e = check_config(2, 3, Fraction(1, 2), Fraction(1, 6))
    checks += 1
    if e:
        errors.append(e)

    # Randomized fuzz.
    for _ in range(2000):
        nrows = rng.randint(1, 8)
        ncols = rng.randint(1, 8)
        hspace = Fraction(rng.random()).limit_denominator(10_000)
        wspace = Fraction(rng.random()).limit_denominator(10_000)
        e = check_config(nrows, ncols, hspace, wspace)
        checks += 1
        if e:
            errors.append(e)
            if len(errors) > 20:
                break

    if errors:
        print(f"G-AX FAIL: {len(errors)} mismatch(es) in {checks} configs. First few:")
        for e in errors[:10]:
            print("  -", e)
        sys.exit(1)

    print(f"G-AX OK: deep model axisExtents == real GridSpec.get_grid_positions "
          f"on {checks} configs (boundary + F2P + fuzz). "
          f"Columns match lefts/rights; rows match reverse(bottoms/tops). "
          f"No consumed axioms to check.")
    sys.exit(0)


if __name__ == "__main__":
    main()
