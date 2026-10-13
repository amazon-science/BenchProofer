"""Twin-artifact model for astropy__astropy-12907.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Two transforms are placed side by side. Each carries a known 0/1 dependency
  matrix relating its outputs (rows) to its inputs (columns): `left` has shape
  `lr x lc` and `right` has shape `rr x rc`. The side-by-side combination
  produces a single dependency matrix of shape `(lr + rr) x (lc + rc)` whose
  rows are laid out as two diagonal blocks:

    * each of the first `lr` rows is the corresponding row of `left` followed
      by `rc` zeros (the upper-left block reproduces `left`, the upper-right
      block is empty);
    * each of the last `rr` rows is `lc` zeros followed by the corresponding
      row of `right` (the lower-left block is empty, the lower-right block
      reproduces `right`).

  The lower-right block therefore carries the *actual* row contents of `right`:
  an input/output pair that `right` reports as independent (entry 0) stays
  independent in the combined matrix, and a dependent pair (entry 1) stays
  dependent. That block is a faithful copy of `right`'s rows, never a constant
  all-ones block.

Matrices are modelled as pure sequences of pure rows, `PSeq[PSeq[int]]` (each
row a `PSeq[int]` of 0/1 entries). Pure sequences carry no heap permission, so
the specification quantifies over rows directly. No library callee is
axiomatized: the combination is a pure block placement, modelled deeply via a
front-recursive row fold and pinned row-by-row by the spec.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# axioms-end


# pure-start
@Pure
def zeros(n: int) -> PSeq[int]:
    """A row of `n` zeros: the empty padding block. Recursively defined, so the
    value is uniquely pinned (it is exactly `n` copies of the literal 0); the
    `is_grid` length obligation needs only its length."""
    Requires(n >= 0)
    Ensures(len(Result()) == n)
    if n == 0:
        return PSeq(0).take(0)
    return zeros(n - 1) + PSeq(0)


@Pure
def is_grid(m: PSeq[PSeq[int]], rows: int, cols: int) -> bool:
    """A well-formed `rows x cols` matrix: `rows` rows, each of length `cols`."""
    return len(m) == rows and Forall(int, lambda k: (
        Implies(0 <= k and k < rows, len(m[k]) == cols), [[m[k]]]))


@Pure
def expected_row(left: PSeq[PSeq[int]], right: PSeq[PSeq[int]],
                 lr: int, lc: int, rr: int, rc: int, i: int) -> PSeq[int]:
    """The `i`-th row of the combined matrix: for an upper row, the matching
    row of `left` padded on the right with `rc` zeros; for a lower row, `lc`
    zeros followed by the matching row of `right` (the actual `right` row, not
    a constant)."""
    Requires(lr >= 0 and lc >= 0 and rr >= 0 and rc >= 0)
    Requires(is_grid(left, lr, lc) and is_grid(right, rr, rc))
    Requires(0 <= i and i < lr + rr)
    Ensures(len(Result()) == lc + rc)
    if i < lr:
        return left[i] + zeros(rc)
    return zeros(lc) + right[i - lr]
# pure-end


def parallel_dependency_matrix(left: PSeq[PSeq[int]], right: PSeq[PSeq[int]],
                               lr: int, lc: int, rr: int, rc: int
                               ) -> PSeq[PSeq[int]]:
    # pre-conditions-start
    Requires(lr >= 0 and lc >= 0 and rr >= 0 and rc >= 0)
    Requires(is_grid(left, lr, lc))
    Requires(is_grid(right, rr, rc))
    # The postconditions are claimed of EVERY run, not only of runs that reach
    # the return: the method must terminate. Level 2, not 1, because the body
    # constructs sequences whose own __init__ carries an obligation and needs
    # room strictly below the caller's level.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The combined matrix has lr + rr rows and lc + rc columns.
    Ensures(is_grid(Result(), lr + rr, lc + rc))
    # Each row is exactly the block-placed row: upper rows extend `left` with
    # trailing zeros; lower rows prepend zeros to the ACTUAL `right` row, so
    # right's independence structure is preserved row by row.
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < lr + rr,
        Result()[i] == expected_row(left, right, lr, lc, rr, rc, i)),
        [[Result()[i]]])))
    # post-conditions-end
    # impl-start
    noutp = lr + rr
    result = PSeq(zeros(0)).take(0)  # type: PSeq[PSeq[int]]
    i = 0
    while i < noutp:
        # invariants-start
        Invariant(is_grid(left, lr, lc))
        Invariant(is_grid(right, rr, rc))
        Invariant(noutp == lr + rr)
        Invariant(0 <= i and i <= noutp)
        Invariant(len(result) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
            len(result[k]) == lc + rc), [[result[k]]])))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
            result[k] == expected_row(left, right, lr, lc, rr, rc, k)),
            [[result[k]]])))
        # At most `noutp - i` iterations remain, and `i` grows by exactly 1 each
        # pass while `noutp` is loop-invariant, so the bound strictly decreases;
        # the `+ 1` keeps it positive on the final pass (0 remaining). The inner
        # ones-block loop's counter `t` is reset on every outer pass, so it must
        # NOT appear here.
        Invariant(MustTerminate(noutp - i + 1))
        # invariants-end
        if i < lr:
            # upper row: left[i] then rc trailing zeros (right block empty).
            row = left[i] + zeros(rc)  # type: PSeq[int]
        else:
            # lower row: lc leading zeros, then the lower-right block filled
            # with a constant 1-block rather than the actual right row.
            block = PSeq(1).take(0)  # type: PSeq[int]
            t = 0
            while t < rc:
                # invariants-start
                Invariant(0 <= t and t <= rc)
                Invariant(len(block) == t)
                # The ones-block loop runs at most `rc - t` more times within
                # THIS outer pass: `t` rises by 1 each pass and `rc` is a
                # parameter (loop-invariant, independent of the outer `i`), so
                # the bound strictly decreases and `+ 1` keeps it positive.
                Invariant(MustTerminate(rc - t + 1))
                # invariants-end
                block = block + PSeq(1)
                t = t + 1
            row = zeros(lc) + block
        Assert(row == expected_row(left, right, lr, lc, rr, rc, i))
        Assert(len(row) == lc + rc)
        old_result = result  # type: PSeq[PSeq[int]]
        result = result + PSeq(row)
        # The append leaves the earlier rows untouched and places `row` at i.
        Assert(len(result) == i + 1)
        Assert(result[i] == row)
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
            result[k] == old_result[k]), [[result[k]]])))
        i = i + 1
    return result
    # impl-end
