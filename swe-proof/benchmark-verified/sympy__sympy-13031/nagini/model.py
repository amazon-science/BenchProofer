"""Twin-artifact model for sympy__sympy-13031.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Two two-dimensional arrays are concatenated along a shared dimension. Each
  array is described by its shape ``(rows, cols)`` together with the population
  of cells it HOLDS -- the cells that carry a value, every other cell reading
  back as the additive zero. Three facets of that population are observed: its
  size ``held``, the sum ``rsum`` of the row indices of the held cells, and the
  sum ``csum`` of their column indices. The two index sums pin WHERE the held
  cells sit, so a result with the right shape and the right NUMBER of held cells
  but with those cells relocated is still not a concatenation.

  (1) Horizontal concatenation places ``b`` to the right of ``a``. The result
      has ``a``'s row count and the SUM of the two column counts. This holds
      even when an operand is degenerate (has zero rows): a chain of
      zero-row arrays must ACCUMULATE columns, so concatenating an already-grown
      zero-row result with another zero-row operand yields the sum of their
      column counts, never just the second operand's column count. The single
      exception is an operand with NO COLUMNS AT ALL: contributing neither a
      column nor a cell, it leaves the result carrying the other operand's own
      shape -- its row count and its column count.

  (2) Vertical concatenation is the exact transpose: ``b`` is placed beneath
      ``a``; the result has ``a``'s column count and the SUM of the two row
      counts, with the symmetric degenerate-operand accumulation rule and the
      symmetric exception for an operand with no rows at all.

  (3) Concatenation is CONTENT-PRESERVING AND PLACEMENT-EXACT, on every path
      including the degenerate ones. The result holds every cell of
      both operands and holds nothing else, so its held-cell count is the SUM of
      the two operands' counts. Moreover the cells taken from ``a`` keep their
      coordinates, while the cells taken from ``b`` are OFFSET along the
      concatenation axis only:

        * horizontal: ``b``'s cells keep their row index and their column index
          moves right by ``a``'s column count. So the result's row-index sum is
          the plain sum of the two operands' row-index sums, and its
          column-index sum is the sum of theirs plus ``a.cols`` once per held
          cell of ``b``.
        * vertical: the transpose -- ``b``'s cells keep their column index and
          their row index moves down by ``a``'s row count.

      Joining an operand that holds nothing onto ``b`` therefore reproduces
      ``b``'s held cells at their ORIGINAL coordinates: a result of the right
      shape whose held cells were discarded is not a concatenation, and neither
      is one that keeps them but puts them somewhere else.

  When the operands disagree on the shared dimension and neither operand
  vanishes along it, concatenation is rejected.

A two-dimensional array is modelled as a minimal class carrying only the
touched facets: its ``rows`` and ``cols`` counts and the three facets of its
held-cell population, ``held`` / ``rsum`` / ``csum`` (all non-negative ints).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class ShapeMismatch(Exception):
    """Raised when the two operands cannot be concatenated because they
    disagree on the shared dimension and no degenerate normalisation applies."""
    pass


class Mat:
    def __init__(self, rows: int, cols: int, held: int, rsum: int,
                 csum: int) -> None:
        Requires(rows >= 0 and cols >= 0 and held >= 0)
        Requires(rsum >= 0 and csum >= 0)
        # Straight-line constructor: terminates at the lowest level, leaving room
        # for every obligated caller above it.
        Requires(MustTerminate(1))
        Ensures(Acc(self.rows) and self.rows == rows)  # type: ignore
        Ensures(Acc(self.cols) and self.cols == cols)  # type: ignore
        Ensures(Acc(self.held) and self.held == held)  # type: ignore
        Ensures(Acc(self.rsum) and self.rsum == rsum)  # type: ignore
        Ensures(Acc(self.csum) and self.csum == csum)  # type: ignore
        self.rows = rows
        self.cols = cols
        self.held = held
        self.rsum = rsum
        self.csum = csum


# axioms-start
# (no @ContractOnly axioms: the unchanged merge callee is modelled deeply as
# plain integer arithmetic on the five facets — see refinement.md A-reference
# rows.)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


def concat_right(a: Mat, b: Mat) -> Mat:
    # pre-conditions-start
    Requires(Acc(a.rows, 1 / 2) and Acc(a.cols, 1 / 2) and Acc(a.held, 1 / 2)
             and Acc(a.rsum, 1 / 2) and Acc(a.csum, 1 / 2))
    Requires(Acc(b.rows, 1 / 2) and Acc(b.cols, 1 / 2) and Acc(b.held, 1 / 2)
             and Acc(b.rsum, 1 / 2) and Acc(b.csum, 1 / 2))
    Requires(a.rows >= 0 and a.cols >= 0 and b.rows >= 0 and b.cols >= 0)
    Requires(a.held >= 0 and b.held >= 0)
    # Index sums of a cell population are sums of non-negative coordinates.
    Requires(a.rsum >= 0 and a.csum >= 0 and b.rsum >= 0 and b.csum >= 0)
    # An array with no columns (or no rows) has no cells, so it holds none.
    Requires(Implies(a.rows == 0 or a.cols == 0, a.held == 0))
    Requires(Implies(b.rows == 0 or b.cols == 0, b.held == 0))
    # An empty cell population sums to zero on both coordinate axes.
    Requires(Implies(a.held == 0, a.rsum == 0 and a.csum == 0))
    Requires(Implies(b.held == 0, b.rsum == 0 and b.csum == 0))
    # TERMINATION (an obligation, not a hint): level 3 where the operands
    # disagree on the shared dimension, level 2 where they agree, both above
    # Mat.__init__ at level 1. A non-terminating implementation does not satisfy
    # this contract.
    Requires(MustTerminate(3 if a.rows != b.rows else 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(a.rows, 1 / 2) and Acc(a.cols, 1 / 2) and Acc(a.held, 1 / 2)
            and Acc(a.rsum, 1 / 2) and Acc(a.csum, 1 / 2))
    Ensures(Acc(b.rows, 1 / 2) and Acc(b.cols, 1 / 2) and Acc(b.held, 1 / 2)
            and Acc(b.rsum, 1 / 2) and Acc(b.csum, 1 / 2))
    Ensures(Acc(Result().rows) and Acc(Result().cols) and Acc(Result().held)
            and Acc(Result().rsum) and Acc(Result().csum))
    # An operand with no columns at all contributes neither a column nor a
    # cell, so the result carries the other operand's row count and its column
    # count. Such an operand is never a ground for rejection.
    Ensures(Implies(a.cols == 0,
                    Result().rows == b.rows and Result().cols == b.cols))
    # Otherwise the rows must agree and the result is a's row count with the
    # SUM of the two column counts (degenerate zero-row operands accumulate).
    Ensures(Implies(a.cols != 0,
                    a.rows == b.rows
                    and Result().rows == a.rows
                    and Result().cols == a.cols + b.cols))
    # CONTENT PRESERVATION, on every returning path: every held cell of both
    # operands survives into the result and none is invented, so the result's
    # held-cell count is the SUM of the operands' counts. In particular a join
    # whose left operand holds nothing reproduces b's cells in full.
    Ensures(Result().held == a.held + b.held)
    # PLACEMENT, on every returning path. Horizontal concatenation moves b's
    # cells along the column axis ONLY, by exactly a's column count, and moves
    # a's cells not at all. So the row-index sum is the plain sum of the two,
    # and the column-index sum picks up a.cols once per held cell of b. Where
    # a's column count is zero the offset is zero, so b's cells keep their own
    # coordinates.
    Ensures(Result().rsum == a.rsum + b.rsum)
    Ensures(Result().csum == a.csum + b.csum + a.cols * b.held)
    # post-conditions-end
    # Disagreement on the shared dimension with no normalisation is rejected.
    Exsures(ShapeMismatch,
            Acc(a.rows, 1 / 2) and Acc(a.cols, 1 / 2) and Acc(a.held, 1 / 2)
            and Acc(a.rsum, 1 / 2) and Acc(a.csum, 1 / 2)
            and Acc(b.rows, 1 / 2) and Acc(b.cols, 1 / 2) and Acc(b.held, 1 / 2)
            and Acc(b.rsum, 1 / 2) and Acc(b.csum, 1 / 2)
            and a.cols != 0 and a.rows != b.rows)
    # impl-start
    if a.cols == 0 and a.rows != b.rows:
        base = Mat(b.rows, 0, 0, 0, 0)  # type: Mat
        return concat_right(base, b)
    if a.rows != b.rows:
        raise ShapeMismatch()
    return Mat(a.rows, a.cols + b.cols, a.held + b.held,
               a.rsum + b.rsum, a.csum + b.csum + a.cols * b.held)
    # impl-end


def concat_below(a: Mat, b: Mat) -> Mat:
    # pre-conditions-start
    Requires(Acc(a.rows, 1 / 2) and Acc(a.cols, 1 / 2) and Acc(a.held, 1 / 2)
             and Acc(a.rsum, 1 / 2) and Acc(a.csum, 1 / 2))
    Requires(Acc(b.rows, 1 / 2) and Acc(b.cols, 1 / 2) and Acc(b.held, 1 / 2)
             and Acc(b.rsum, 1 / 2) and Acc(b.csum, 1 / 2))
    Requires(a.rows >= 0 and a.cols >= 0 and b.rows >= 0 and b.cols >= 0)
    Requires(a.held >= 0 and b.held >= 0)
    # Index sums of a cell population are sums of non-negative coordinates.
    Requires(a.rsum >= 0 and a.csum >= 0 and b.rsum >= 0 and b.csum >= 0)
    # An array with no columns (or no rows) has no cells, so it holds none.
    Requires(Implies(a.rows == 0 or a.cols == 0, a.held == 0))
    Requires(Implies(b.rows == 0 or b.cols == 0, b.held == 0))
    # An empty cell population sums to zero on both coordinate axes.
    Requires(Implies(a.held == 0, a.rsum == 0 and a.csum == 0))
    Requires(Implies(b.held == 0, b.rsum == 0 and b.csum == 0))
    # TERMINATION (an obligation, not a hint): the transpose of concat_right's
    # measure -- level 3 where the operands disagree on the shared dimension,
    # level 2 where they agree, both above Mat.__init__ at level 1. A
    # non-terminating implementation does not satisfy this contract.
    Requires(MustTerminate(3 if a.cols != b.cols else 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(a.rows, 1 / 2) and Acc(a.cols, 1 / 2) and Acc(a.held, 1 / 2)
            and Acc(a.rsum, 1 / 2) and Acc(a.csum, 1 / 2))
    Ensures(Acc(b.rows, 1 / 2) and Acc(b.cols, 1 / 2) and Acc(b.held, 1 / 2)
            and Acc(b.rsum, 1 / 2) and Acc(b.csum, 1 / 2))
    Ensures(Acc(Result().rows) and Acc(Result().cols) and Acc(Result().held)
            and Acc(Result().rsum) and Acc(Result().csum))
    # An operand with no rows at all contributes neither a row nor a cell, so
    # the result carries the other operand's column count and its row count.
    # Such an operand is never a ground for rejection.
    Ensures(Implies(a.rows == 0,
                    Result().cols == b.cols and Result().rows == b.rows))
    # Otherwise the cols must agree and the result is a's column count with the
    # SUM of the two row counts (degenerate zero-column operands accumulate).
    Ensures(Implies(a.rows != 0,
                    a.cols == b.cols
                    and Result().cols == a.cols
                    and Result().rows == a.rows + b.rows))
    # CONTENT PRESERVATION, on every returning path: every held cell of both
    # operands survives into the result and none is invented, so the result's
    # held-cell count is the SUM of the operands' counts. In particular a join
    # whose upper operand holds nothing reproduces b's cells in full.
    Ensures(Result().held == a.held + b.held)
    # PLACEMENT, on every returning path — the transpose of concat_right's rule.
    # Vertical concatenation moves b's cells along the row axis ONLY, by exactly
    # a's row count, and moves a's cells not at all. So the column-index sum is
    # the plain sum of the two, and the row-index sum picks up a.rows once per
    # held cell of b. Where a's row count is zero the offset is zero, so b's
    # cells keep their own coordinates.
    Ensures(Result().csum == a.csum + b.csum)
    Ensures(Result().rsum == a.rsum + b.rsum + a.rows * b.held)
    # post-conditions-end
    # Disagreement on the shared dimension with no normalisation is rejected.
    Exsures(ShapeMismatch,
            Acc(a.rows, 1 / 2) and Acc(a.cols, 1 / 2) and Acc(a.held, 1 / 2)
            and Acc(a.rsum, 1 / 2) and Acc(a.csum, 1 / 2)
            and Acc(b.rows, 1 / 2) and Acc(b.cols, 1 / 2) and Acc(b.held, 1 / 2)
            and Acc(b.rsum, 1 / 2) and Acc(b.csum, 1 / 2)
            and a.rows != 0 and a.cols != b.cols)
    # impl-start
    if a.rows == 0 and a.cols != b.cols:
        base = Mat(0, b.cols, 0, 0, 0)  # type: Mat
        return concat_below(base, b)
    if a.cols != b.cols:
        raise ShapeMismatch()
    return Mat(a.rows + b.rows, a.cols, a.held + b.held,
               a.rsum + b.rsum + a.rows * b.held, a.csum + b.csum)
    # impl-end
