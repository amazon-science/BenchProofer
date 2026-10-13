# Requirements: honour `wspace`/`hspace` in `Figure.subfigures`

## Introduction

`matplotlib.figure.FigureBase.subfigures` arranges a regular grid of
`SubFigure` panels inside a parent figure (or subfigure). The method accepts
`wspace` and `hspace` parameters that are documented to reserve horizontal and
vertical space between adjacent subfigures, expressed as a fraction of the
average subfigure width/height.

In the affected version these two parameters have no effect: the produced
subfigures are laid out edge-to-edge (filling the parent's unit square) no
matter what `wspace`/`hspace` are passed, because the grid spacing computed by
the backing `GridSpec` is discarded when each `SubFigure`'s relative bounding
box is set at construction time. The goal is to make `subfigures` actually
place the panels with the requested gaps between them, so that changing
`wspace`/`hspace` changes the panel rectangles.

The layout is a tiling of the parent's unit square `[0,1] × [0,1]` in
figure-fraction coordinates. Along a direction holding `k` panels with spacing
`s`, every panel gets the same extent `c = 1 / (k + s·(k − 1))` and adjacent
panels are separated by a gap of `s·c`. Columns are numbered left-to-right
starting at the left edge; rows are numbered top-to-bottom starting at the top
edge. Each `SubFigure` exposes its physical rectangle through its `bbox`
attribute (`bbox.min` = lower-left, `bbox.max` = upper-right, in device/pixel
coordinates = figure-fraction extent scaled by the figure width/height).

Affected module/function: `lib/matplotlib/figure.py`, method
`FigureBase.subfigures` (and the per-panel `SubFigure` relative-bbox update it
drives). The grid geometry itself is provided by
`matplotlib.gridspec.GridSpec.get_grid_positions`.

## Requirement 1: Reserve requested spacing between subfigures

**User story:** As a user creating a grid of subfigures, I want `wspace` and
`hspace` to reserve proportional gaps between the panels, so that the layout I
request is the layout I get.

**Acceptance criteria**

1. WHEN `subfigures(nrows, ncols, wspace=w, hspace=h)` is called on a figure
   that has no layout engine and at least one of `w`, `h` is not `None`, THEN
   `subfigures` SHALL position every returned `SubFigure` so that its rectangle
   reflects the requested spacing rather than filling the parent edge-to-edge.
2. WHEN a horizontal spacing `w` is applied to a grid with `ncols` columns,
   THEN each column SHALL be given the common figure-fraction width
   `c_w = 1 / (ncols + w·(ncols − 1))`, and adjacent columns SHALL be separated
   by a horizontal gap of `w·c_w`.
3. WHEN a vertical spacing `h` is applied to a grid with `nrows` rows, THEN each
   row SHALL be given the common figure-fraction height
   `c_h = 1 / (nrows + h·(nrows − 1))`, and adjacent rows SHALL be separated by
   a vertical gap of `h·c_h`.
4. WHEN the grid is laid out, THEN column `i` (0-based, left edge = column 0)
   SHALL have its left edge at figure-fraction `i·(c_w + w·c_w)` and its right
   edge one column-width `c_w` further to the right.
5. WHEN the grid is laid out, THEN row `j` (0-based, top edge = row 0) SHALL
   have its top edge at figure-fraction `1 − j·(c_h + h·c_h)` and its bottom
   edge one row-height `c_h` below that top edge.
6. The system SHALL express each panel's rectangle in the parent's physical
   coordinates by scaling the figure-fraction left/right by the figure width
   and the figure-fraction bottom/top by the figure height; i.e. for a panel
   occupying fractional extents `[x0, x1] × [y0, y1]` on a figure of width `W`
   and height `H`, its `bbox.min` SHALL equal `(x0·W, y0·H)` and its `bbox.max`
   SHALL equal `(x1·W, y1·H)`.
7. WHEN the panels and gaps are laid out, THEN the leftmost column's left edge
   SHALL be at fraction 0, the rightmost column's right edge at fraction 1, the
   top row's top edge at fraction 1, and the bottom row's bottom edge at
   fraction 0, so the panels together with the gaps exactly fill the parent's
   unit square.
8. WHILE distinct spacing values are requested, the resulting panel rectangles
   SHALL differ accordingly, so that a larger `wspace`/`hspace` shrinks the
   panels and widens the gaps.

## Requirement 2: Default behaviour with no spacing requested

**User story:** As a user who does not pass `wspace`/`hspace`, I want the
previous edge-to-edge behaviour preserved so existing code is unaffected.

**Acceptance criteria**

1. IF both `wspace` and `hspace` are `None` (not supplied) and the figure has
   no layout engine, THEN `subfigures` SHALL leave no space between panels: the
   panels SHALL tile the parent's unit square edge-to-edge with no gaps.
2. WHEN neither spacing is supplied and no layout engine is in use, THEN column
   `i` SHALL span figure-fraction `[i/ncols, (i+1)/ncols]` and row `j` SHALL
   span figure-fraction `[1 − (j+1)/nrows, 1 − j/nrows]` (equal-sized,
   gapless panels).
3. The system SHALL keep the documented meaning that, when a spacing value is
   not given, spacing is inferred from rcParams only when a constrained layout
   engine is in use, and is zero when no layout engine is in use.

## Requirement 3: Preserve existing subfigure grid structure and API

**User story:** As a maintainer, I want the spacing fix to leave the rest of
the `subfigures` contract intact, so that no existing behaviour regresses.

**Acceptance criteria**

1. WHEN `subfigures(nrows, ncols)` is called, THEN it SHALL return the panels
   arranged as an `nrows × ncols` grid, indexable in row-major order where
   index `[j, i]` selects the panel in row `j` (from the top) and column `i`
   (from the left).
2. The system SHALL continue to honour `squeeze`: WHEN `squeeze` is true and the
   grid has a single panel it SHALL return that panel directly, and WHEN
   `squeeze` is true it SHALL drop length-1 dimensions from the returned array;
   otherwise it SHALL return a 2-D array of panels.
3. The system SHALL continue to honour `width_ratios` and `height_ratios` when
   supplied, dividing the available width/height among columns/rows in those
   proportions before the spacing gaps are applied.
4. WHEN each panel is created, THEN it SHALL remain a fully functional
   `SubFigure` whose own subplots and artists render within the panel's
   rectangle, and applying the spacing SHALL only reposition/resize the panel
   without otherwise altering it.
5. The system SHALL apply the spacing adjustment only when no layout engine is
   active; WHEN a layout engine (e.g. constrained layout) manages the figure,
   `subfigures` SHALL NOT impose these fixed gap positions and SHALL leave panel
   placement to that engine.
