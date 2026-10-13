#!/usr/bin/env python3
"""G-AX executable soundness check for matplotlib__matplotlib-25960.

There is NO consumed @ContractOnly axiom in model.py (the axioms region is
empty). The one kind-A obligation is an **A-reference**: the deep geometry model
in model.py (`col_left`, `col_right`, `row_top`, `row_bottom`, plus the
normalization equations pinning the common cell width / height) must equal the
REAL grid-position routine the gold patch invokes:

    matplotlib.gridspec.GridSpec.get_grid_positions(fig)

as used by the corrected `Figure.subfigures`, i.e. with the gridspec spanning the
full figure (`left=0, right=1, bottom=0, top=1`) and the requested `wspace` /
`hspace`. This script runs that REAL routine (in-container, where matplotlib is
installed) on boundary + randomized inputs and asserts every observed cell
extent equals the closed-form the model pins. Exit 0 iff sound.

Model closed-form (equal row/column ratios; the F2P test's configuration):
  cw = 1 / (ncols + wspace*(ncols-1))         # normalized column width
  ch = 1 / (nrows + hspace*(nrows-1))         # normalized row height
  col_left(i)   = i*cw*(1+wspace)
  col_right(i)  = col_left(i) + cw
  row_top(j)    = 1 - j*ch*(1+hspace)         # j counted from the TOP
  row_bottom(j) = row_top(j) - ch

`get_grid_positions` returns (bottoms, tops, lefts, rights) as arrays; we check
the model's per-cell extents against those array entries.

Two tolerances, deliberately. The per-cell comparison uses abs_tol=1e-9: it asks
whether the R closed form is the right DESCRIPTION of the routine, and a rounding
difference is not a counterexample to that. The grid ORIGIN is checked bit-exactly
instead, because that is the one place the R<->float64 bridge has no tolerance to
spend (refinement.md C.1): the coordinate comparison the instance grades with is
relative with no absolute part, so an expected figure edge of 0.0 admits no
deviation at all. The closing edges close only up to rounding, so they are
reported rather than asserted.

The rendering discipline itself is measured here too, rather than argued in prose.
mapping.md 2 states the condition every R step of the refinement has to meet: the
step's float64 evaluation must denote the real value the model's step denotes.
That condition is what decides how a refinement renders the model's arithmetic,
and the two candidate renderings are distinguishable, so both are measured:

  * READING each extent from `get_grid_positions` meets the condition -- which is
    why the deep geometry is tagged an A-reference rather than an identical
    operation.
  * RE-DERIVING the closed form in float64 does not meet it. On the configuration
    the instance grades, the routine closes the bottom row at exactly 0.0 while
    the re-derived expression lands at -1.11e-16; the graded coordinate comparison
    is relative with no absolute part, so against an expected 0.0 that difference
    is unbounded. `check_rendering_discipline` asserts the two renderings
    disagree there, and the per-grid loop reports how often they agree
    bit-for-bit.
  * A real-zero addend or a real-one factor, rendered by the float64 literal that
    denotes it (`+ 0.0`, `* 1.0`, `/ 1.0`), is a bit-exact no-op on every
    coordinate the routine produces. That is a one-line arithmetic fact, and it is
    asserted on every observed coordinate so that refinement.md C.1's statement
    about that class of rival spellings rests on a measurement instead of on the
    reader's agreement.

The model's normalization equations are measured on the routine too, for the same
reason. Those equations are the R-refinement of `cell_w`/`cell_h` (mapping.md 2,
refinement.md A3): rather than a reciprocal the model carries `cw`, `ch` as inputs
PINNED by `cw*(ncols+wspace*(ncols-1))==1` and its row analogue. The abstraction
claims the routine's own cell width and height satisfy those equations, and they
do -- but in `float64` only up to rounding, not identically. Both halves of that
are asserted: the residual stays within a few ulp on every grid (so the linear
pinning is the right description of the division), and on the graded grid it is
NONZERO. The second half is what makes the precondition itself a source of the
subterms refinement.md C.1 is about: `cw*ncols + cw*wspace*(ncols-1) - 1` is a
real zero on every input the precondition admits, so it is invisible to every
clause of the contract, while its float64 value on the graded grid is -1.11e-16.
The condition therefore has to be stated on the whole class, not on literal
algebra alone.
"""
import math
import random
import sys


# The configuration the instance's F2P test builds (2 rows, 3 columns,
# wspace=1/6, hspace=0.5). Named because the rendering-discipline leg is about
# what the graded comparison admits, which is a property of this grid.
GRADED = (2, 3, 1 / 6., 0.5)

# Slack allowed on the model's normalization equations when they are evaluated on
# the routine's own float64 cell width / height. The equations hold exactly over
# the reals; each side here is a handful of roundings away from its real value, so
# the bound is stated in ulps of 1 rather than as a physical tolerance. Widened
# from the worst observed (4.5 ulp) to leave room for a different libm without
# leaving room for a genuinely different normalization.
ULP = 2.220446049250313e-16
RESIDUAL_ULPS = 64


def model_extents(nrows, ncols, j, i, wspace, hspace):
    """The model.py closed-form extents of cell (row j from top, column i).

    Evaluated in float64, so this doubles as the RE-DERIVED rendering of the
    model's steps -- the one mapping.md 2's condition excludes.
    """
    cw = 1.0 / (ncols + wspace * (ncols - 1))
    ch = 1.0 / (nrows + hspace * (nrows - 1))
    left = i * cw * (1.0 + wspace)
    right = left + cw
    top = 1.0 - j * ch * (1.0 + hspace)
    bottom = top - ch
    return left, bottom, right, top


def grid_positions(nrows, ncols, wspace, hspace):
    """Run the REAL routine under the gold patch's configuration and return
    (bottoms, tops, lefts, rights)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec

    fig = plt.figure()
    gs = GridSpec(nrows=nrows, ncols=ncols, figure=fig,
                  wspace=wspace, hspace=hspace,
                  left=0, right=1, bottom=0, top=1)
    positions = gs.get_grid_positions(fig)
    plt.close(fig)
    return positions


def normalization_residual(nrows, ncols, wspace, hspace,
                           bottoms, tops, lefts, rights):
    """How far the routine's own cell width / height miss the model's pinning
    equations when those are evaluated in float64.

    The cell width the model calls `cw` is the routine's `cell_w`, recovered the
    way a refinement recovers it -- as the first column's width, READ off the
    extents the routine returned. Likewise `ch`. Zero over the reals; returned so
    the caller can both bound it and show it is not always zero.
    """
    cw = float(rights[0]) - float(lefts[0])
    ch = float(tops[0]) - float(bottoms[0])
    width_residual = cw * ncols + cw * wspace * (ncols - 1.0) - 1.0
    height_residual = ch * nrows + ch * hspace * (nrows - 1.0) - 1.0
    return width_residual, height_residual


def check_against_real(nrows, ncols, wspace, hspace):
    """Run the REAL GridSpec.get_grid_positions and assert it equals the model
    closed-form for every cell, under the gold patch's configuration
    (left=0, right=1, bottom=0, top=1, equal ratios)."""
    bottoms, tops, lefts, rights = grid_positions(nrows, ncols, wspace, hspace)

    tol = 1e-9
    # Whether the RE-DERIVED rendering happens to agree bit-for-bit with the
    # rendering that reads from the routine, on this grid.
    same_rendering = True
    worst_rendering = 0.0
    for j in range(nrows):
        for i in range(ncols):
            m_left, m_bottom, m_right, m_top = model_extents(
                nrows, ncols, j, i, wspace, hspace)
            r_left = lefts[i]
            r_right = rights[i]
            r_bottom = bottoms[j]
            r_top = tops[j]
            for name, m, r in (("left", m_left, r_left),
                               ("right", m_right, r_right),
                               ("bottom", m_bottom, r_bottom),
                               ("top", m_top, r_top)):
                assert math.isclose(m, r, rel_tol=0, abs_tol=tol), (
                    "deep geometry model unsound: nrows=%d ncols=%d j=%d i=%d "
                    "wspace=%r hspace=%r %s: model=%r real=%r"
                    % (nrows, ncols, j, i, wspace, hspace, name, m, r))
                if m != float(r):
                    same_rendering = False
                    worst_rendering = max(worst_rendering, abs(m - float(r)))

    # Where the instance's graded coordinate comparison expects an exact figure
    # edge it admits NO deviation: the comparison is relative with no absolute
    # part, so against an expected 0.0 every nonzero difference is infinitely far
    # off. The two extents the model pins to the ORIGIN of each axis -- the first
    # column's left and the first row's top -- are therefore checked bit-exactly
    # rather than within `tol`. The routine reaches them exactly by construction
    # (the interleaved cumulative sum opens with a zero separator, so
    # `lefts[0] = left + 0` and `tops[0] = top - 0`), and that exactness is what
    # refinement.md C.1 rests on where it has no tolerance to spend -- so it is
    # measured here rather than assumed. If the routine ever reached the origin
    # through arithmetic that rounds, this is where that should surface, not in a
    # downstream coordinate comparison.
    assert lefts[0] == 0.0, (
        "grid origin not exact: nrows=%d ncols=%d wspace=%r hspace=%r "
        "lefts[0]=%r" % (nrows, ncols, wspace, hspace, lefts[0]))
    assert tops[0] == 1.0, (
        "grid origin not exact: nrows=%d ncols=%d wspace=%r hspace=%r "
        "tops[0]=%r" % (nrows, ncols, wspace, hspace, tops[0]))

    # The rendering condition's other side, on every coordinate this grid
    # produces: a subterm whose real value is 0 (additive) or 1 (multiplicative
    # or divisive), rendered by the float64 literal that denotes that value,
    # moves no coordinate at all. Arithmetically this is one line; it is asserted
    # because refinement.md C.1 uses it to classify a whole family of rival
    # spellings, and a claim a gate can check should not be left to prose.
    noop = 0
    for arr in (bottoms, tops, lefts, rights):
        for value in arr:
            v = float(value)
            assert v + 0.0 == v and v - 0.0 == v, (
                "real-zero addend is not a no-op at %r (nrows=%d ncols=%d "
                "wspace=%r hspace=%r)" % (v, nrows, ncols, wspace, hspace))
            assert v * 1.0 == v and v / 1.0 == v, (
                "real-one factor is not a no-op at %r (nrows=%d ncols=%d "
                "wspace=%r hspace=%r)" % (v, nrows, ncols, wspace, hspace))
            noop += 1

    # A3's normalization equations, evaluated on the routine's own cell width and
    # height. Bounded, not asserted zero: the equations pin `cw`/`ch` over the
    # reals, and the routine reaches them through a division and a cumulative sum,
    # so a few ulp of residual is what a faithful refinement of a real division
    # looks like. A residual outside the bound would mean the routine normalizes
    # to something other than a unit total, which WOULD refute the abstraction.
    width_residual, height_residual = normalization_residual(
        nrows, ncols, wspace, hspace, bottoms, tops, lefts, rights)
    residual = max(abs(width_residual), abs(height_residual))
    assert residual <= RESIDUAL_ULPS * ULP, (
        "normalization equation not satisfied by the real cell size: nrows=%d "
        "ncols=%d wspace=%r hspace=%r residual=%r (%.1f ulp, bound %d)"
        % (nrows, ncols, wspace, hspace, residual, residual / ULP,
           RESIDUAL_ULPS))

    # The CLOSING edges (last column's right, bottom row's bottom) close only up
    # to rounding, so they are reported rather than asserted exact. The caller
    # folds them into the report line, and refinement.md C.1 cites the measured
    # spread as the reason a refinement must READ those extents from the routine
    # instead of re-deriving them from the closed form in float64.
    closing = max(abs(float(rights[-1]) - 1.0), abs(float(bottoms[-1])))
    return closing, same_rendering, worst_rendering, noop, residual


def check_rendering_discipline():
    """Assert the two candidate renderings of the model's steps are
    distinguishable exactly where the graded comparison has no tolerance to
    spend, on the configuration the instance grades.

    This is the measurement mapping.md 2 and refinement.md C.1 rest on. It says
    nothing about which program is correct; it says that "refine each step so its
    float64 value denotes the real value the model's step denotes" is a condition
    with teeth here, because the alternative -- transcribing the closed form into
    float64 -- misses the figure edge the instance grades against exactly 0.0.
    """
    nrows, ncols, wspace, hspace = GRADED
    bottoms, tops, lefts, rights = grid_positions(nrows, ncols, wspace, hspace)
    read_bottom = float(bottoms[-1])
    rederived_bottom = model_extents(
        nrows, ncols, nrows - 1, 0, wspace, hspace)[1]
    assert read_bottom == 0.0, (
        "extents READ from the routine do not close the graded grid exactly: "
        "bottoms[-1]=%r" % (read_bottom,))
    assert rederived_bottom != read_bottom, (
        "the two renderings agree on the graded grid's closing edge (%r); the "
        "rendering condition refinement.md C.1 states would then be idle here "
        "and its consequences need re-deriving" % (rederived_bottom,))

    # The precondition is itself a source of the subterms C.1 classifies. Its
    # normalization equation is a real zero on every admissible input -- so no
    # clause of the contract can see a term built from it -- while in float64 on
    # this very grid it is not zero. Asserted nonzero so that C.1's claim about
    # precondition-derived subterms is a measurement here rather than prose, and so
    # that a matplotlib whose division happened to come out exact would flag the
    # claim for re-derivation instead of silently making it idle.
    width_residual, height_residual = normalization_residual(
        nrows, ncols, wspace, hspace, bottoms, tops, lefts, rights)
    assert width_residual != 0.0, (
        "the graded grid's width normalization residual is exactly zero; the "
        "precondition-derived half of refinement.md C.1's class would then be "
        "idle on the graded configuration and needs re-deriving")
    return read_bottom, rederived_bottom, width_residual, height_residual


def main():
    # --- boundary cases ----------------------------------------------------
    boundary = [
        (2, 3, 1 / 6., 0.5),   # the F2P test configuration
        (1, 1, 0.0, 0.0),
        (1, 1, 0.5, 0.5),      # single cell: spacing has no neighbour to gap
        (2, 2, 0.0, 0.0),      # zero gap: cells abut
        (2, 2, 0.2, 0.2),
        (3, 1, 0.0, 1.0),
        (1, 3, 1.0, 0.0),
        (4, 5, 0.3, 0.7),
        (2, 2, 1.0, 1.0),
        (5, 5, 0.05, 0.05),
    ]
    grids = 0
    exact_closing = 0
    worst_closing = 0.0
    same_rendering = 0
    worst_rendering = 0.0
    noop_values = 0
    worst_residual = 0.0
    nonzero_residual = 0

    def record(result):
        nonlocal grids, exact_closing, worst_closing
        nonlocal same_rendering, worst_rendering, noop_values
        nonlocal worst_residual, nonzero_residual
        closing, same, worst, noop, residual = result
        grids += 1
        exact_closing += (closing == 0.0)
        worst_closing = max(worst_closing, closing)
        same_rendering += bool(same)
        worst_rendering = max(worst_rendering, worst)
        noop_values += noop
        worst_residual = max(worst_residual, residual)
        nonzero_residual += (residual != 0.0)

    for nrows, ncols, wspace, hspace in boundary:
        record(check_against_real(nrows, ncols, wspace, hspace))

    # --- randomized fuzz ---------------------------------------------------
    rng = random.Random(25960)
    for _ in range(400):
        nrows = rng.randint(1, 6)
        ncols = rng.randint(1, 6)
        wspace = rng.choice([0.0, rng.uniform(0.0, 2.0)])
        hspace = rng.choice([0.0, rng.uniform(0.0, 2.0)])
        record(check_against_real(nrows, ncols, wspace, hspace))

    read_bottom, rederived_bottom, graded_width_residual, _ = (
        check_rendering_discipline())

    print("G-AX OK: deep geometry model (col_left/col_right/row_top/row_bottom "
          "+ normalization) == real GridSpec.get_grid_positions on %d boundary "
          "+ 400 fuzz grids (left=0,right=1,bottom=0,top=1, equal ratios); grid "
          "origin (lefts[0], tops[0]) bit-exact on all %d; closing edges "
          "(rights[-1], bottoms[-1]) bit-exact on %d/%d, worst closing "
          "deviation %.3g. Rendering discipline: on the graded grid the extents "
          "READ from the routine close the bottom row at exactly %r while the "
          "closed form re-derived in float64 lands at %r; the two renderings "
          "agree bit-for-bit on %d/%d grids (worst disagreement %.3g); a "
          "real-zero addend / real-one factor rendered by its float64 literal "
          "moves none of the %d observed coordinates. Normalization (A3): the "
          "routine's own cell width/height satisfy the model's pinning equations "
          "to within %.1f ulp on every grid (bound %d), and NOT identically -- "
          "the residual is nonzero on %d/%d grids and is %r on the graded grid, "
          "so the precondition supplies real-zero subterms of its own."
          % (len(boundary), grids, exact_closing, grids, worst_closing,
             read_bottom, rederived_bottom, same_rendering, grids,
             worst_rendering, noop_values, worst_residual / ULP,
             RESIDUAL_ULPS, nonzero_residual, grids, graded_width_residual))
    return 0


if __name__ == "__main__":
    sys.exit(main())
