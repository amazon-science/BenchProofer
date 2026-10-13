# Requirements: correct column placement in `Matrix.col_insert`

## Introduction

Inserting one or more columns into a matrix with `Matrix.col_insert(pos, other)`
(implemented via the `_eval_col_insert` helper in `sympy/matrices/common.py`,
and inherited by the concrete matrix classes) currently misplaces the host
matrix's original columns that lie to the right of the insertion point. When a
block of columns is inserted at position `pos`, the columns of the original
matrix that originally sat at or after `pos` are read from the wrong source
column, so they appear shifted (e.g. rows/values scrambled) instead of simply
being pushed rightward by the width of the inserted block.

The goal is that `col_insert` produces a matrix in which the inserted columns
occupy the requested position and every original column is preserved exactly,
merely relocated by the number of inserted columns. This document specifies the
observable behavior of `col_insert` and the surrounding argument handling that
must be preserved.

The affected module is `sympy/matrices/common.py`; the relevant public API is
`Matrix.col_insert` (and its helper `_eval_col_insert`).

## Requirement 1: Correct placement of columns to the right of the insertion point

**User story:** As a user inserting columns into a matrix, I want the original
columns that follow the insertion point to be preserved and simply shifted
right, so that `col_insert` does not corrupt my data.

**Acceptance criteria**

1. WHEN a matrix `self` with `n` columns has another matrix `other` with `k`
   columns inserted at column position `pos` (with `0 <= pos <= n`), THEN the
   resulting matrix SHALL have `n + k` columns and the same number of rows as
   `self`.
2. WHEN the result is queried at a column index `j` with `j < pos`, THEN the
   entry at every row `i` SHALL equal the original entry of `self` at row `i`,
   column `j`.
3. WHEN the result is queried at a column index `j` with `pos <= j < pos + k`,
   THEN the entry at every row `i` SHALL equal the entry of `other` at row `i`,
   column `j - pos`.
4. WHEN the result is queried at a column index `j` with `j >= pos + k`, THEN
   the entry at every row `i` SHALL equal the original entry of `self` at row
   `i`, column `j - k` (i.e. the host column it occupied before insertion,
   shifted right by exactly the number of inserted columns `k`).
5. IF an identity or otherwise structured matrix has a block of columns inserted
   in its interior, THEN the portion of the original matrix appearing to the
   right of the inserted block SHALL retain its original per-row values in every
   row (no rows of the right-hand portion are reordered, dropped, or duplicated).

## Requirement 2: Argument handling for the insertion position

**User story:** As a user, I want `col_insert` to accept convenient position
arguments so that I can insert at the ends or with negative indexing.

**Acceptance criteria**

1. IF `pos` is negative, THEN `col_insert` SHALL interpret it relative to the
   end of the matrix by adding the column count, and any position that is still
   negative after this adjustment SHALL be treated as `0`.
2. IF `pos` is greater than the number of columns of `self`, THEN `col_insert`
   SHALL treat the position as equal to the number of columns of `self` (append
   at the right end).
3. WHEN `pos` equals `0`, THEN the inserted columns SHALL appear at the left of
   the result and all original columns SHALL follow them unchanged.
4. WHEN `pos` equals the number of columns of `self`, THEN all original columns
   SHALL appear first, unchanged, followed by the inserted columns.

## Requirement 3: Shape validation and degenerate inputs

**User story:** As a user, I want `col_insert` to reject mismatched shapes and
to handle an empty host, so that misuse fails clearly and edge cases still work.

**Acceptance criteria**

1. IF the number of rows of `other` differs from the number of rows of `self`
   (and `self` is non-empty), THEN `col_insert` SHALL raise a shape error rather
   than return a matrix.
2. IF `self` is an empty (null) matrix, THEN `col_insert` SHALL return a matrix
   equal to `other`.
3. The system SHALL return a matrix of the same concrete matrix type as `self`.

## Requirement 4: Preserve existing insertion and related behaviors (regression)

**User story:** As a maintainer, I want the fix to change only the misplaced
right-hand columns and leave all other matrix construction behavior intact, so
that existing functionality keeps working.

**Acceptance criteria**

1. The system SHALL keep the behavior of `row_insert` unchanged: inserting rows
   at a position places the inserted rows at that position and shifts the
   original lower rows down by the number of inserted rows, preserving all
   values.
2. The system SHALL keep the behavior of column and row joining
   (`row_join`/`col_join`) unchanged, appending the second matrix's columns or
   rows after the first without altering existing entries.
3. WHEN `col_insert` is used on the examples documented for the function, THEN
   the produced matrix SHALL match the documented result.
4. The system SHALL preserve the results of `col_insert` on symbolic and
   numeric matrices alike, computing each output entry purely from the two input
   operands at the column indices described in Requirement 1.
