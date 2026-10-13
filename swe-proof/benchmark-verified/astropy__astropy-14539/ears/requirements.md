# Requirements: correct diffing of 64-bit variable-length-array table columns

## Introduction

`astropy.io.fits` provides `FITSDiff` (and the `printdiff` convenience
function) for reporting differences between two FITS files, delegating the
table-data comparison to `TableDataDiff` in `astropy/io/fits/diff.py`. For each
common table column, `TableDataDiff._diff` selects one of several comparison
strategies according to the column's storage kind and records the differing
rows into `diff_values`, `diff_total`, and `diff_ratio`.

FITS stores variable-length arrays (VLAs) using a descriptor whose format code
is `P` (32-bit descriptors) or `Q` (64-bit descriptors). The comparison logic
recognises the `P` descriptor kind and compares such columns row by row
(comparing each row's whole variable-length sequence), but it does **not**
recognise the `Q` descriptor kind. As a result, a `Q`-format VLA column falls
through to the ordinary flat element-by-element comparison, which is not valid
for ragged per-row sequences: it can spuriously report a column — and therefore
a whole file — as different even when the two inputs are byte-for-byte
identical (for example, comparing a file that contains a `Q`-format VLA column
to itself).

The goal is to make VLA column comparison treat the 64-bit (`Q`) descriptor
kind exactly the same way as the 32-bit (`P`) descriptor kind, so that
identical inputs never report a difference and genuine per-row differences are
reported correctly, while all previously supported column kinds keep behaving
as before.

## Requirement 1: 64-bit VLA columns use the row-wise comparison strategy

**User story:** As a user comparing FITS files that contain 64-bit
variable-length-array columns, I want those columns compared row by row like
their 32-bit counterparts, so that diffs are accurate.

**Acceptance criteria**

1. WHEN `TableDataDiff` compares a common column whose FITS format denotes a
   variable-length array — of either the 32-bit descriptor kind or the 64-bit
   descriptor kind — and the column is not floating-point-typed, THEN
   `TableDataDiff` SHALL compare the two columns row by row, treating each
   row's entire variable-length sequence as the unit of comparison.
2. WHEN a variable-length-array column is compared row by row, THEN
   `TableDataDiff` SHALL count a row as differing only when that row's whole
   sequence in the first column is not equal (within the configured relative
   and absolute tolerances) to the corresponding row's sequence in the second
   column.
3. The system SHALL apply this row-wise comparison to the 64-bit descriptor
   kind under the same conditions and with the same per-row semantics it
   already applies to the 32-bit descriptor kind.

## Requirement 2: identical inputs never report a difference

**User story:** As a user, I want comparing a file (or table) to an identical
one to report no differences, so that I can trust a "no differences" result.

**Acceptance criteria**

1. WHEN two tables are element-for-element identical and at least one column is
   a 64-bit-descriptor variable-length-array column, THEN `TableDataDiff` SHALL
   report the tables as identical, with a total difference count of zero and a
   difference ratio of zero.
2. WHEN a FITS file containing a 64-bit-descriptor variable-length-array column
   is compared to itself via `FITSDiff` (or `printdiff`), THEN the comparison
   SHALL report no data differences.
3. WHEN two tables contain the same set of columns, THEN every such column
   (including 32-bit and 64-bit variable-length-array columns) SHALL be treated
   as a common column and be included in the common-column set used for
   comparison.

## Requirement 3: genuine per-row VLA differences are reported correctly

**User story:** As a user, I want real differences in variable-length-array
columns to be reported with the correct rows and totals, so that the diff is
complete and its summary is accurate.

**Acceptance criteria**

1. WHEN a variable-length-array column (32-bit or 64-bit descriptor kind)
   contains rows whose sequences differ between the two tables, THEN
   `TableDataDiff` SHALL record each differing row as a single recorded
   difference identified by the column name together with that row's index,
   paired with the two rows' sequence values from the first and second tables.
2. WHEN differences are recorded, THEN the recorded per-row differences SHALL
   preserve the column-by-column, then increasing-row-index ordering in which
   the columns and rows are compared, so that a 64-bit-descriptor VLA column's
   differing rows appear after those of the columns compared before it.
3. WHEN differences exist across the compared columns, THEN `TableDataDiff`
   SHALL set the total difference count to the number of differing
   (column, row) elements, counting each differing row of each column once.
4. WHEN the total difference count is known, THEN `TableDataDiff` SHALL compute
   the difference ratio as the total difference count divided by the total
   number of table data elements (the number of rows multiplied by the number
   of columns).
5. WHEN a difference report is produced, THEN the report text SHALL state the
   number of differing table-data elements and the corresponding percentage
   consistent with the computed difference ratio.

## Requirement 4: previously supported column kinds are unaffected

**User story:** As a maintainer, I want the change scoped to adding 64-bit VLA
support, so that no existing comparison behavior regresses.

**Acceptance criteria**

1. The system SHALL keep comparing 32-bit-descriptor variable-length-array
   columns row by row exactly as before.
2. The system SHALL keep comparing floating-point-typed columns using the
   tolerance-based closeness comparison and all other (fixed-shape, non-VLA)
   columns using the ordinary element-by-element comparison.
3. WHEN tables mix ordinary columns (logical, bit, byte, integer, real,
   complex, and 32-bit VLA columns) with a 64-bit VLA column, THEN
   `TableDataDiff` SHALL report the identical-vs-different verdict, the total
   difference count, the difference ratio, and the recorded per-row
   differences correctly across all of them together.
