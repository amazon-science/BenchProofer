# Requirements: Consistent `mincnt` behavior in `Axes.hexbin`

## Introduction

`matplotlib.axes.Axes.hexbin` (in `lib/matplotlib/axes/_axes.py`) accepts a
`mincnt` parameter that controls which hexagonal cells are drawn based on how
many input data points fall into each cell. Internally `hexbin` has two code
paths: one used when the optional `C` value array is **not** supplied (cell
values are point counts), and one used when `C` **is** supplied (cell values are
produced by applying `reduce_C_function` to the `C` values that fall in the
cell).

The two paths applied `mincnt` inconsistently. When `C` was omitted, a cell was
displayed when its point count was greater than or equal to `mincnt`. When `C`
was supplied, a cell was displayed only when its point count was strictly
greater than `mincnt`. As a result, for the same data, grid, and `mincnt`, the
set of displayed cells differed depending solely on whether `C` was passed —
e.g. with `mincnt=1`, cells holding exactly one point were shown in the
no-`C` case but dropped in the `C` case.

The goal is to make the `mincnt` threshold semantics identical on both paths:
in every case a cell is displayed when its point count is **at least** `mincnt`.

## Requirement 1: Uniform `mincnt` threshold semantics

**User story:** As a user of `hexbin`, I want `mincnt` to mean the same thing
whether or not I pass a `C` array, so that supplying `C` never silently changes
which cells appear in the plot.

**Acceptance criteria**

1. WHEN `hexbin` is called with a `C` value array and an integer `mincnt`, THEN
   `hexbin` SHALL include (assign a reduced value to, rather than discard) every
   hexagonal cell whose number of contained data points is greater than or equal
   to `mincnt`.
2. WHEN `hexbin` is called with a `C` value array and an integer `mincnt`, THEN
   `hexbin` SHALL discard (leave with no value, so it is not drawn) every
   hexagonal cell whose number of contained data points is strictly less than
   `mincnt`.
3. WHEN a cell holds a number of data points exactly equal to a supplied
   integer `mincnt` and `C` is supplied, THEN `hexbin` SHALL include that cell
   and assign it the value produced by applying `reduce_C_function` to the
   cell's `C` values.
4. IF the same data points, grid, extent, and an integer `mincnt` of at least
   one are used, THEN the set of cells `hexbin` displays SHALL be identical
   whether or not a `C` value array is supplied. (At such a threshold every
   qualifying cell contains at least one data point, so the `C`-path reduction
   is applied only to non-empty collections and does not remove any cell the
   no-`C` path keeps.)
5. WHEN a cell is included on the `C`-supplied path, THEN its value SHALL be
   exactly the result of applying `reduce_C_function` to the list of `C` values
   for the points in that cell, unchanged from prior behavior.

## Requirement 2: Preserve existing `mincnt` and no-`C` behavior

**User story:** As an existing user, I want the previously correct behaviors of
`hexbin` to remain unchanged, so that the fix corrects only the inconsistency
and introduces no regressions.

**Acceptance criteria**

1. WHEN `hexbin` is called without a `C` value array and with an integer
   `mincnt`, THEN `hexbin` SHALL continue to display exactly those cells whose
   point count is greater than or equal to `mincnt`.
2. IF `mincnt` is `None` (its default), THEN `hexbin` SHALL apply no minimum
   point-count threshold, treating the required minimum count as zero so that a
   cell qualifies whenever its point count is greater than or equal to zero. On
   the no-`C` path this is unchanged: every cell within the grid is displayed,
   including cells whose point count is zero. On the `C`-supplied path a cell is
   no longer required to contain at least one data point before it is
   considered: `reduce_C_function` is applied to every cell's (possibly empty)
   collection of `C` values, and a cell is omitted only when that reduction
   yields NaN. Consequently, at the `None`/zero threshold an empty cell now
   appears on the `C`-supplied path whenever `reduce_C_function` maps an empty
   input to a non-NaN value, whereas previously every empty cell was dropped on
   that path regardless of `reduce_C_function`.
3. The system SHALL preserve, for every displayed cell, its position, the number
   and ordering of the returned cell values, and the reduction result on the
   `C`-supplied path, changing only which cells are kept versus dropped at the
   `mincnt` boundary.
4. WHEN `hexbin` completes, THEN it SHALL return a `PolyCollection` describing
   the hexagonal bins, with all other documented behavior of `hexbin`
   (gridding, extents, scales, marginals, coloring) unchanged.
