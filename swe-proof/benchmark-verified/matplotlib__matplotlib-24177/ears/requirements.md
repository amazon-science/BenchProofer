# Requirements: Patch data limits must enclose the whole path when autoscaling

## Introduction

When a `Patch` (for example a `matplotlib.patches.PathPatch`, or the polyline
patches produced by `Axes.hist` with `histtype='step'`) is added to an Axes,
matplotlib expands the Axes data limits so that autoscaling frames the artist.
This happens in `Axes._update_patch_limits` (`lib/matplotlib/axes/_base.py`),
which walks the patch's `Path` segment by segment via `Path.iter_bezier`,
collects representative points along each segment (segment endpoints plus any
interior axis-aligned extrema of curved segments), stacks them, transforms them
to data coordinates, and passes them to `update_datalim`, which grows the data
limits to the componentwise bounding box of those points.

The bug: `Path.iter_bezier` forwards keyword arguments to `Path.iter_segments`,
whose `simplify` argument defaults to `None`, which resolves to the path's
`should_simplify` attribute. When path simplification is active (the default
`rcParams['path.simplify']` with a positive `path.simplify_threshold`),
`iter_segments` drops vertices that the line-simplification heuristic judges not
to change the rendered appearance. During limit computation this is wrong: a
dropped vertex can be the one attaining the path's extent, so the computed
bounding box is too small and autoscaling clips the artist. The reported
symptom is a `hist` `histtype='step'` density axis that fails to auto-scale to
the tallest bins, but the underlying defect affects any patch whose path is
simplified during limit collection — especially paths with many closely spaced,
small-magnitude points.

The goal is to make `_update_patch_limits` collect points from the *unsimplified*
path so that the data-limit bounding box encloses every defining point of the
path, while leaving unrelated limit-update behavior intact.

## Requirement 1: Data limits enclose the full extent of an added patch's path

**User story:** As a user adding a patch to an Axes and calling autoscale, I want
the resulting view limits to contain the entire path, so that no part of the
artist is clipped regardless of how densely or finely its vertices are spaced.

**Acceptance criteria**
1. WHEN a patch whose path is a polyline (straight line segments through a
   sequence of defining points) is added to an Axes on a standard rectilinear
   projection and the Axes is autoscaled, THEN the Axes data limits SHALL span
   at least from the minimum to the maximum of the path's defining point
   coordinates along each axis — i.e. the lower x limit SHALL be less than or
   equal to the smallest x among the defining points, the upper x limit SHALL be
   greater than or equal to the largest x, and likewise for y.
2. WHEN the path contains many closely spaced points and some points have
   small magnitude relative to the path's overall extent (the configuration in
   which line simplification would otherwise discard interior vertices), THEN the
   computed data limits SHALL still enclose the point of maximum extent along
   each axis, so that autoscaling does not clip the path.
3. The system SHALL determine the patch's contribution to the data limits from
   the path's full, unsimplified set of segments, so that no defining vertex is
   omitted from the limit computation because it was deemed visually redundant.
4. WHEN `Path.iter_bezier` is asked to iterate a path with simplification
   explicitly disabled, THEN it SHALL yield a bezier segment for every segment of
   the path without dropping any vertex, forwarding the request to disable
   simplification through to the underlying segment iteration.

## Requirement 2: Per-segment extrema are still included for curved paths

**User story:** As a user adding a patch containing curved (quadratic or cubic)
segments, I want the data limits to include the true extremes of each curve, so
that curved artists are also framed correctly.

**Acceptance criteria**
1. WHEN a patch's path contains curved segments, THEN `_update_patch_limits`
   SHALL include, for each segment, the segment's start and end points together
   with any interior axis-aligned extrema of that segment when growing the data
   limits.
2. WHEN a path segment is a straight line or a single point, THEN the points
   contributed to the data limits SHALL be that segment's own endpoints (no
   spurious interior points).

## Requirement 3: Preserve existing patch-limit exclusions and coordinate handling

**User story:** As a maintainer, I want this fix to change only which vertices
are collected, not the surrounding limit-update rules, so that existing behavior
is not regressed.

**Acceptance criteria**
1. IF the added patch is a rectangle with both zero width and zero height, THEN
   `_update_patch_limits` SHALL NOT update the data limits for it (the existing
   exclusion that keeps zero-size hist bins from disturbing scaling is retained).
2. The system SHALL apply the patch's transform when mapping the collected
   points into data coordinates, and SHALL update only the axis (x, y, or both)
   whose branch of the patch transform actually maps into the data transform.
3. WHILE the Axes uses a non-rectilinear projection, the system SHALL retain its
   existing rule of not updating the data limit along an axis whose patch
   transform matches that axis's blended transform (as for `axvspan`/`axhspan`).
4. WHEN a patch has an empty path (no vertices), THEN `_update_patch_limits`
   SHALL leave the data limits unchanged.

## Requirement 4: Existing autoscale behavior for other patches is unaffected

**User story:** As a user, I want patches that were already framed correctly to
keep behaving the same, so that the fix is a strict improvement.

**Acceptance criteria**
1. The system SHALL continue to expand data limits to enclose the extremes of
   bezier-curve patches that already autoscaled correctly, producing the same
   view limits as before for those patches.
2. WHEN multiple patches are added to an Axes, THEN the autoscaled data limits
   SHALL enclose the union of all their paths' extents along each axis.
