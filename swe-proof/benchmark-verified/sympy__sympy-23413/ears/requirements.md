# Requirements: Hermite Normal Form must not drop rows of tall integer matrices

## Introduction

The integer Hermite Normal Form (HNF) routine reachable through
`sympy.matrices.normalforms.hermite_normal_form` and its lower-level engine
`sympy.polys.matrices.normalforms.hermite_normal_form` /
`_hermite_normal_form` (in `sympy/polys/matrices/normalforms.py`) computes a
column-style HNF of a matrix of integers over the domain `ZZ`. The algorithm
works one row at a time from the bottom row upward, placing pivots into the
rightmost columns and tracking the leftmost column into which a pivot has so
far been placed; the reported result is the block of columns from that
leftmost pivot column onward.

A defect caused the routine to consider only the bottom-most rows of a matrix
that has more rows than columns. When such a matrix has genuine pivot
contributions coming from its upper rows, those pivots were never placed, so
the result was falsely treated as rank-deficient and valid columns/rows were
dropped. For example, a user attempting a row-style HNF via flips and
transposes on `[[5, 8, 12], [0, 0, 1]]` expected a result equivalent to
`[[5, 8, 0], [0, 0, 1]]` but instead received a result with a row removed.

The goal is that every row of the input is eligible to contribute a pivot, so
that no genuine pivot column is dropped, while preserving the existing HNF of
all inputs that were already handled correctly.

## Requirement 1: Every row is eligible to contribute a pivot

**User story:** As a user computing the Hermite Normal Form of an integer
matrix that has more rows than columns, I want all rows to be examined for
pivots, so that pivots contributed by upper rows are not silently discarded.

**Acceptance criteria**

1. WHEN `hermite_normal_form` is called on an integer matrix whose number of
   rows exceeds its number of columns, THEN the routine SHALL process rows from
   the bottom row upward such that any row may contribute a pivot column, not
   only the bottom-most rows.
2. WHEN the input has more rows than columns and one or more of its upper rows
   carry independent pivot content, THEN the returned HNF SHALL retain a pivot
   column for each such contribution rather than omitting it.
3. IF the input is an integer matrix that, before this correction, had a
   genuine pivot column dropped because it lay above the bottom `min(rows, columns)`
   band, THEN the returned HNF SHALL now include that pivot column.
4. WHEN a tall integer matrix has exactly one nonzero row located above the
   bottom band and the remaining rows are zero, THEN the returned HNF SHALL be
   a single-column matrix whose entries reflect that row's normalized pivot
   (the pivot placed in that row, zeros in the other rows) rather than an
   empty-width matrix.

## Requirement 2: Correct pivot count and result width

**User story:** As a caller relying on the shape of the HNF, I want the number
of reported pivot columns to be correct, so that downstream code sees neither
spurious empty results nor out-of-range column indices.

**Acceptance criteria**

1. The system SHALL return, as the HNF, exactly the columns from the leftmost
   successfully-placed pivot column onward.
2. WHILE processing rows, IF every column already holds a pivot (the leftmost
   pivot pointer has reached the first column), THEN the routine SHALL stop
   examining further rows, because no additional pivot can be placed.
3. WHEN the input has more rows than columns and pivots have been placed in all
   of its columns, THEN the returned HNF SHALL have exactly as many columns as
   the input has columns and SHALL NOT attempt to place a pivot beyond the
   available columns.
4. WHEN the input is processed, THEN the number of pivot columns reported SHALL
   equal the number of rows that actually contributed a new pivot, and no valid
   pivot column SHALL be omitted from the result.

## Requirement 3: Preserve existing correct behavior (regression protection)

**User story:** As an existing user of the HNF routine, I want all previously
correct results to remain unchanged, so that this correction fixes only the
row-dropping defect.

**Acceptance criteria**

1. WHEN `hermite_normal_form` is called on an integer matrix whose number of
   columns is greater than or equal to its number of rows, THEN the returned
   HNF SHALL be identical to the result produced before this correction.
2. WHEN a square or wide integer matrix of full row rank is supplied, THEN the
   returned HNF SHALL be the same lower-triangular-style normal form as before,
   with pivots in the rightmost columns.
3. WHEN the transpose of such a matrix (producing a taller-than-wide matrix) is
   supplied, THEN the returned HNF SHALL match the previously accepted result
   for that transposed input.
4. IF a pivot entry would be negative, THEN the routine SHALL normalize it so
   the reported pivot is non-negative, and SHALL reduce the entries to the
   right of each pivot modulo that pivot as before.
5. WHEN the optional multiple-of-determinant argument `D` is supplied for a
   matrix of full row rank (with or without the rank check enabled), THEN the
   routine SHALL return the same HNF as the ordinary algorithm for that input.
6. IF the matrix is not over the integer domain `ZZ`, THEN the routine SHALL
   raise the existing domain error rather than returning a result.
7. WHEN an all-zero row or a row contributing no pivot is encountered, THEN the
   routine SHALL leave the leftmost pivot pointer unchanged for that row (so the
   same column is still targeted for the next row upward) and SHALL NOT report a
   spurious pivot column for it.
