# Requirements: Correct shape when stacking dimension-degenerate matrices

## Introduction

Stacking matrices edge-to-edge is provided by the sparse-matrix join
operations in `sympy/matrices/sparse.py` — `SparseMatrix.row_join` (append a
matrix to the right, `[A B]`) and `SparseMatrix.col_join` (append a matrix
beneath, `[A; B]`) — together with the `hstack`/`vstack` class methods that
fold a sequence of matrices through `row_join`/`col_join` respectively.

Both join methods contained an over-broad shortcut: whenever the left/top
operand held no stored elements (i.e. either of its dimensions was zero) the
operand was silently dropped and the other operand was returned unchanged.
As a consequence, horizontally stacking a run of matrices that all have zero
rows but increasing column counts (e.g. shapes `0x0, 0x1, 0x2, 0x3`) discarded
the already-accumulated columns and produced the width of the last operand
alone instead of the sum of all widths; the vertical case had the symmetric
defect for matrices with zero columns.

The goal is that a matrix with a degenerate dimension (zero rows or zero
columns) contributes correctly to a join: its non-degenerate dimension still
adds up, and a degenerate operand never causes the other operand's
contribution to be thrown away. Non-degenerate joins, the resulting matrix
class, and the shape-mismatch error behavior must all be preserved.

## Requirement 1: Horizontal joining accumulates total column count

**User story:** As a user assembling a matrix left-to-right, I want
`row_join`/`hstack` to sum the column counts of all operands even when some
operands have zero rows, so that the assembled matrix has the correct width.

**Acceptance criteria**

1. WHEN two matrices that share the same number of rows are joined
   horizontally, THEN the result SHALL have that same number of rows and a
   number of columns equal to the sum of the two operands' column counts.
2. WHEN `hstack` is invoked on a sequence of matrices that all share the same
   number of rows, THEN the result SHALL have that shared number of rows and a
   number of columns equal to the sum of the column counts of every operand in
   the sequence.
3. WHEN a sequence of matrices that each have zero rows and column counts
   `0, 1, 2, 3` is joined horizontally, THEN the result SHALL have zero rows
   and exactly six columns, and SHALL NOT collapse to the width of any single
   operand.
4. WHEN two matrices with equal row counts are joined horizontally, THEN in the
   result the leftmost columns SHALL hold the entries of the left operand and
   the remaining columns SHALL hold the entries of the right operand, shifted
   right by the left operand's column count.

## Requirement 2: Horizontal joining tolerates a column-empty operand

**User story:** As a user, I want a matrix that has zero columns to be joinable
to the right of, or with, another matrix regardless of a row-count difference,
so that an empty accumulator does not raise or drop the other operand.

**Acceptance criteria**

1. IF the left operand has zero columns and its row count differs from the
   right operand's row count, THEN the horizontal join SHALL return a matrix
   whose shape and entries equal those of the right operand (its row count and
   column count taken from the right operand).
2. WHEN the left operand has zero columns and its row count already equals the
   right operand's row count, THEN the horizontal join SHALL behave as an
   ordinary join, yielding a result with the shared row count and the summed
   column count.

## Requirement 3: Vertical joining accumulates total row count

**User story:** As a user assembling a matrix top-to-bottom, I want
`col_join`/`vstack` to sum the row counts of all operands even when some
operands have zero columns, so that the assembled matrix has the correct
height.

**Acceptance criteria**

1. WHEN two matrices that share the same number of columns are joined
   vertically, THEN the result SHALL have that same number of columns and a
   number of rows equal to the sum of the two operands' row counts.
2. WHEN `vstack` is invoked on a sequence of matrices that all share the same
   number of columns, THEN the result SHALL have that shared number of columns
   and a number of rows equal to the sum of the row counts of every operand in
   the sequence.
3. WHEN a sequence of matrices that each have zero columns and row counts
   `0, 1, 2, 3` is joined vertically, THEN the result SHALL have zero columns
   and exactly six rows, and SHALL NOT collapse to the height of any single
   operand.
4. WHEN two matrices with equal column counts are joined vertically, THEN in
   the result the topmost rows SHALL hold the entries of the top operand and
   the remaining rows SHALL hold the entries of the bottom operand, shifted
   down by the top operand's row count.

## Requirement 4: Vertical joining tolerates a row-empty operand

**User story:** As a user, I want a matrix that has zero rows to be joinable
beneath, or with, another matrix regardless of a column-count difference, so
that an empty accumulator does not raise or drop the other operand.

**Acceptance criteria**

1. IF the top operand has zero rows and its column count differs from the
   bottom operand's column count, THEN the vertical join SHALL return a matrix
   whose shape and entries equal those of the bottom operand (its row count and
   column count taken from the bottom operand).
2. WHEN the top operand has zero rows and its column count already equals the
   bottom operand's column count, THEN the vertical join SHALL behave as an
   ordinary join, yielding a result with the shared column count and the summed
   row count.

## Requirement 5: Preserve matrix class and shape-mismatch errors

**User story:** As a maintainer, I want joins to keep returning the left/top
operand's concrete matrix class and to keep rejecting genuinely incompatible
shapes, so that existing behavior and callers are not regressed.

**Acceptance criteria**

1. The system SHALL return a result whose concrete matrix class is the same as
   that of the left operand for a horizontal join and the top operand for a
   vertical join, including when the returned values come from the other
   operand.
2. IF two matrices are joined horizontally, the left operand has a nonzero
   number of columns, and their row counts differ, THEN the operation SHALL
   raise a shape-mismatch error.
3. IF two matrices are joined vertically, the top operand has a nonzero number
   of rows, and their column counts differ, THEN the operation SHALL raise a
   shape-mismatch error.
4. WHEN both operands are non-degenerate and compatible, THEN the join SHALL
   keep producing the same combined shape and entries as before this change,
   preserving all previously working stacking, element-access, and related
   sparse-matrix operations.
