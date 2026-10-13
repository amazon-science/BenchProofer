# Requirements: Colorbar separator edges at extended extremities

## Introduction

Matplotlib's colorbar (`matplotlib.colorbar.Colorbar` in
`lib/matplotlib/colorbar.py`) can separate its adjacent color bands with drawn
black lines when the colorbar is created with `drawedges=True`. These separator
lines are stored as segments on the colorbar's `dividers` line collection and
are (re)computed inside the `_add_solids` method from the colorbar's X/Y band
boundary mesh.

When a colorbar is *extended* — i.e. drawn with a triangular or rectangular
end-cap at one or both ends via `extend='min'`, `extend='max'`, or
`extend='both'` — the boundary between the extension region and the first/last
interior color band is an open end. Currently `_add_solids` always discards the
first and last rows of the boundary mesh when building the separators (keeping
only the strictly interior boundaries), so the separator lines at extended
(open) extremities are never drawn even though `drawedges=True`. The reported
bug is that with `drawedges=True` and `extend='both'` the black edges at the two
extremities are missing.

The goal is to make the separator selection keep the terminal boundary segment
at any *open* (extended) end, while continuing to omit the terminal boundary at
any *closed* (non-extended) end, and to draw no separators at all when
`drawedges` is `False`. Whether an end is open is already determined by the
colorbar's `_extend_lower()` and `_extend_upper()` helpers (which also account
for an inverted long axis). This change is localized to the separator-segment
selection in `Colorbar._add_solids`; the rest of the colorbar's drawing,
extension shapes, ticks, and positioning must be unaffected.

## Requirement 1: Draw separator edges at open (extended) extremities

**User story:** As a user creating a colorbar with `drawedges=True` and an
`extend` that opens one or both ends, I want the separator line at each opened
extremity to be drawn, so that every color band — including the extension
end-caps — is visually bounded by an edge.

**Acceptance criteria**
1. WHEN a filled colorbar is drawn with `drawedges=True`, THEN the colorbar
   SHALL populate its `dividers` collection with one separator segment for each
   band boundary that is kept, taken in order from the boundary mesh used to
   draw the color bands.
2. IF `drawedges=True` and the lower end of the colorbar is open (extended at
   the lower end as reported by `_extend_lower()`), THEN the separator at the
   lower extremity (the first boundary row of the mesh) SHALL be included in the
   drawn separators.
3. IF `drawedges=True` and the upper end of the colorbar is open (extended at
   the upper end as reported by `_extend_upper()`), THEN the separator at the
   upper extremity (the last boundary row of the mesh) SHALL be included in the
   drawn separators.
4. WHEN a colorbar is drawn with `drawedges=True` and `extend='both'`, THEN the
   drawn separators SHALL include the separators at BOTH the lower and upper
   extremities in addition to every interior boundary separator.
5. WHEN a colorbar is drawn with `drawedges=True` and `extend='min'`, THEN the
   drawn separators SHALL include the separator at the lower extremity and every
   interior boundary separator, and SHALL NOT include the separator at the upper
   extremity.
6. WHEN a colorbar is drawn with `drawedges=True` and `extend='max'`, THEN the
   drawn separators SHALL include the separator at the upper extremity and every
   interior boundary separator, and SHALL NOT include the separator at the lower
   extremity.

## Requirement 2: Omit separators at closed (non-extended) extremities

**User story:** As a user, I want extremities that are not extended to keep
their prior appearance, so that the outer edge of a closed end is not doubled by
an internal separator line.

**Acceptance criteria**
1. IF `drawedges=True` and the lower end of the colorbar is closed (not extended
   at the lower end), THEN the first boundary row of the mesh SHALL be excluded
   from the drawn separators.
2. IF `drawedges=True` and the upper end of the colorbar is closed (not extended
   at the upper end), THEN the last boundary row of the mesh SHALL be excluded
   from the drawn separators.
3. WHEN a colorbar is drawn with `drawedges=True` and `extend='neither'` (both
   ends closed), THEN the drawn separators SHALL consist of exactly the interior
   boundary separators, excluding both the first and last boundary rows — i.e.
   the separator selection SHALL be identical to the prior behavior for a
   non-extended colorbar.

## Requirement 3: Respect an inverted long axis when deciding open ends

**User story:** As a user with an inverted colorbar axis, I want the correct
physical extremity treated as open, so that the added edges appear at the
extended ends regardless of axis orientation.

**Acceptance criteria**
1. The system SHALL determine which extremities are open using the same
   openness definition applied elsewhere in the colorbar (`_extend_lower()` and
   `_extend_upper()`), which already accounts for the long axis being inverted.
2. WHEN the long axis is inverted, THEN the terminal separators SHALL still be
   kept at the extremities that are open and omitted at the extremities that are
   closed, consistent with Requirements 1 and 2.

## Requirement 4: No separators when drawedges is disabled

**User story:** As a user who did not request edges, I want no separator lines
drawn, so that colorbars without `drawedges` are visually unchanged.

**Acceptance criteria**
1. WHEN a colorbar is drawn with `drawedges=False`, THEN the `dividers`
   collection SHALL contain no separator segments, regardless of the `extend`
   setting.

## Requirement 5: Preserve existing colorbar drawing and extension behavior

**User story:** As a maintainer, I want this change to affect only which
separator segments are drawn, so that all other colorbar behavior continues to
work.

**Acceptance criteria**
1. The system SHALL continue to draw the extension end-cap shapes (triangular by
   default, rectangular when `extendrect=True`) and the colorbar outline for
   `extend='min'`, `extend='max'`, and `extend='both'` exactly as before.
2. The system SHALL leave the color bands, their orientation (horizontal or
   vertical), tick locations, tick labels, and axes positioning unaffected by
   the separator-selection change.
3. WHEN `drawedges=False` and the colorbar has a large number of boundaries,
   THEN the solid color mesh SHALL still be rasterized as before.
4. The system SHALL preserve the existing separator styling (color and line
   width taken from the axes edge color and line width) for the drawn segments.
