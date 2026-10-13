"""Twin-artifact model for matplotlib__matplotlib-25960.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A rectangular grid of sub-regions tiles a unit figure. The caller supplies a
  requested fraction of width and of height to reserve as the gaps BETWEEN the
  sub-regions of one row / column, expressed as a fraction of the average
  sub-region width / height (`wspace`, `hspace`). When those gap fractions are
  given, the placement of every sub-region MUST honour them: the columns are
  separated by horizontal gaps and the rows by vertical gaps, with the cells
  equally sized and the whole grid still spanning the full unit figure
  [0, 1] x [0, 1].

  Concretely, the common column width `cw` is the positive number for which the
  `ncols` columns plus the `(ncols-1)` gaps (each of width `wspace*cw`) exactly
  fill the unit interval, i.e.  cw*(ncols + wspace*(ncols-1)) == 1; symmetrically
  the common row height `ch` satisfies  ch*(nrows + hspace*(nrows-1)) == 1. Then

    * column i (0-based, left to right) starts at  i*cw*(1+wspace)  and ends one
      cell-width later (so consecutive columns are separated by a gap wspace*cw);
    * row j (0-based, counted from the TOP) has its top edge at
      1 - j*ch*(1+hspace)  and its bottom edge one cell-height below (so
      consecutive rows are separated by a gap hspace*ch).

  The guarantees the issue demands:
    * the first column starts exactly at the left edge (0) and the last column
      ends exactly at the right edge (1); the top row's top edge is exactly 1
      and the bottom row's bottom edge is exactly 0 (the grid fills the figure);
    * with a positive requested width gap there is a strictly positive
      horizontal gap between consecutive columns (the right edge of column i is
      strictly less than the left edge of column i+1), and likewise a strictly
      positive vertical gap between consecutive rows when the requested height
      gap is positive. A zero requested gap leaves no gap (the cells abut).
    * the placement is DELIVERED for every admissible grid and in-range cell:
      it is a finite computation that always yields its rectangle. Laying out a
      grid asks for the placement of each of its cells in turn, so a placement
      that merely would-be-correct-if-it-ever-answered honours none of the above.

  Counts and indices are carried as the real numbers they denote (column count
  `ncols >= 1`, row count `nrows >= 1`, column index `0 <= i <= ncols-1`, row
  index `0 <= j <= nrows-1`, all integer-valued). The extents, gap fractions and
  the two normalized cell sizes are interpreted real numbers (verified with
  `--float-encoding=real`) because the placement IS a real-valued geometric
  computation the tests probe to floating tolerance. The two cell sizes enter as
  positive inputs PINNED by their normalization equations above (they are the
  reciprocal-normalized sizes the grid uses); the placement is then the
  spelled-out per-cell linear arithmetic, validated == the real grid-position
  routine out-of-band by axiom_check.py (G-AX), not consumed as an axiom (the
  axioms region is empty).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (none — the modelled delta is the spelled-out cell/gap geometry over reals;
# no opaque library callee is consumed inside an Ensures. The deep geometry
# model is validated == the real grid-position routine by axiom_check.py /
# G-AX. See mapping.md §3.)
# axioms-end


# pure-start
@Pure
def col_left(i: float, wspace: float, cw: float) -> float:
    """Left edge of column `i` (0-based, left to right): `i` whole steps of one
    column width plus one gap each."""
    return i * cw * (1.0 + wspace)


@Pure
def col_right(i: float, wspace: float, cw: float) -> float:
    """Right edge of column `i` (one cell-width past its left edge)."""
    return col_left(i, wspace, cw) + cw


@Pure
def row_top(j: float, hspace: float, ch: float) -> float:
    """Top edge of row `j` (0-based, counted from the top of the figure)."""
    return 1.0 - j * ch * (1.0 + hspace)


@Pure
def row_bottom(j: float, hspace: float, ch: float) -> float:
    """Bottom edge of row `j` (one cell-height below its top edge)."""
    return row_top(j, hspace, ch) - ch
# pure-end


class CellRect:
    """The placement rectangle of one grid cell: the horizontal extent
    [left, right] and the vertical extent [bottom, top]."""

    def __init__(self, left: float, bottom: float, right: float, top: float) -> None:
        Requires(left == left and bottom == bottom and right == right and top == top)
        Requires(MustTerminate(2))
        Ensures(Acc(self.left) and Acc(self.bottom) and Acc(self.right) and Acc(self.top))
        Ensures(self.left == left)
        Ensures(self.bottom == bottom)
        Ensures(self.right == right)
        Ensures(self.top == top)
        self.left = left      # type: float
        self.bottom = bottom  # type: float
        self.right = right    # type: float
        self.top = top        # type: float


def grid_cell_placement(nrows: float, ncols: float, j: float, i: float,
                        wspace: float, hspace: float,
                        cw: float, ch: float) -> CellRect:
    # pre-conditions-start
    # A genuine grid and an in-range cell (row j from the top, column i); the
    # counts and indices are the integer-valued reals they denote.
    Requires(nrows >= 1.0 and ncols >= 1.0)
    Requires(0.0 <= j and j <= nrows - 1.0)
    Requires(0.0 <= i and i <= ncols - 1.0)
    # Requested gap fractions are non-negative (zero means "no gap").
    Requires(wspace >= 0.0)
    Requires(hspace >= 0.0)
    # The common column width / row height are positive and normalized so that
    # all the columns/rows plus their gaps exactly fill the unit interval. (They
    # are the reciprocal-normalized cell sizes the grid is built from.)
    Requires(cw > 0.0)
    Requires(ch > 0.0)
    Requires(cw * (ncols + wspace * (ncols - 1.0)) == 1.0)
    Requires(ch * (nrows + hspace * (nrows - 1.0)) == 1.0)
    # The placement is a TOTAL computation, not merely a partially correct one:
    # for every admissible grid and in-range cell it must DELIVER the rectangle
    # described below, i.e. reach a normal return after finitely many steps. A
    # caller tiling a grid of sub-regions gets an answer for each of them, so a
    # placement that never yields one honours nothing the guarantees below say.
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().left) and Acc(Result().bottom)
            and Acc(Result().right) and Acc(Result().top))
    # The cell occupies exactly the requested-gap-aware extents of cell (j, i).
    Ensures(Result().left == col_left(i, wspace, cw))
    Ensures(Result().right == col_right(i, wspace, cw))
    Ensures(Result().bottom == row_bottom(j, hspace, ch))
    Ensures(Result().top == row_top(j, hspace, ch))
    # The grid fills the figure: leftmost column starts at 0, rightmost ends at
    # 1; the top row's top is 1 and the bottom row's bottom is 0.
    Ensures(Implies(i == 0.0, Result().left == 0.0))
    Ensures(Implies(i == ncols - 1.0, Result().right == 1.0))
    Ensures(Implies(j == 0.0, Result().top == 1.0))
    Ensures(Implies(j == nrows - 1.0, Result().bottom == 0.0))
    # A positive requested width gap leaves a strictly positive horizontal gap
    # between this column and the next: the requested spacing is honoured, not
    # ignored.
    Ensures(Implies(wspace > 0.0 and i <= ncols - 2.0,
                    Result().right < col_left(i + 1.0, wspace, cw)))
    # Likewise a positive requested height gap leaves a strictly positive
    # vertical gap between this row and the one below it.
    Ensures(Implies(hspace > 0.0 and j <= nrows - 2.0,
                    row_top(j + 1.0, hspace, ch) < Result().bottom))
    # post-conditions-end
    # impl-start
    # Pre-patch placement: the requested width/height gaps are NOT accounted
    # for — the cells are laid out abutting (the gap-separation factor is
    # dropped), so the spacing the caller asked for has no effect on the
    # geometry. (This is the behaviour the issue reports: same figure regardless
    # of the requested spacing.)
    left = i * cw
    right = left + cw
    top = 1.0 - j * ch
    bottom = top - ch
    return CellRect(left, bottom, right, top)
    # impl-end
