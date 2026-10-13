# Requirements: Preserve requested axis-limit direction on all scales

## Introduction

Matplotlib lets a user set the visible coordinate range of an axis by calling
the limit-setter methods `set_xlim` / `set_ylim` on a 2-D axes
(`matplotlib.axes._base._AxesBase`) and `set_xlim3d` / `set_ylim3d` /
`set_zlim3d` on a 3-D axes (`mpl_toolkits.mplot3d.axes3d.Axes3D`). A user can
request an *inverted* (descending) axis by passing the endpoints in decreasing
order — a larger lower/left argument than the upper/right one — instead of the
usual increasing order.

Before the requested range is committed to the view limits, each limit-setter
runs the two endpoints through two normalizing steps:

* the singularity-avoiding endpoint normalizer obtained from the axis's major
  locator (`axis.get_major_locator().nonsingular(v0, v1)`), which expands a
  degenerate (zero-width) range so the two endpoints become distinct; and
* the scale-domain restriction `axis.limit_range_for_scale(v0, v1)`, which
  clamps the endpoints to the domain the current scale permits.

Starting in matplotlib 3.1.0, requesting a descending range on a log-scaled
axis (whose major locator is a `LogLocator`, so `Locator.nonsingular` is
reached) no longer inverted the axis: the descending order requested through
the limits was silently discarded during normalization and the axis came out
ascending, even though the same request correctly inverted a linear axis.

The goal is that the *direction* the caller requests survives normalization on
every scale: if the caller passes the endpoints in decreasing order the
committed range stays descending (inverted); if in increasing order it stays
ascending. The endpoint magnitudes must remain exactly the two values produced
by the normalizing steps — only their order may be adjusted to match the
requested direction. The direction is preserved by having each limit-setter
remember whether the caller passed the endpoints in decreasing order and
restore that order after the normalizing steps run, while the locator's
singularity-avoiding normalizer itself returns its two endpoints in increasing
order so that this restoration is deterministic.

## Requirement 1: Preserve a requested descending (inverted) axis range on any scale

**User story:** As a plotting user, I want to invert an axis by passing its
limits in decreasing order and have the inversion take effect regardless of the
axis scale, so that `set_ylim(top, bottom)` inverts the axis for a log scale
just as it already does for a linear scale.

**Acceptance criteria**

1. WHEN `set_xlim`/`set_ylim` is called with two finite endpoints given in
   decreasing order (the first argument strictly greater than the second),
   THEN the axis's committed view interval SHALL be descending (its first/lower
   argument stored as the interval's high end and its second/upper argument as
   the low end), so that the corresponding `get_xlim`/`get_ylim` returns the
   endpoints in the same decreasing order the caller supplied.
2. WHEN `set_ylim` is called with two positive endpoints in decreasing order on
   a log-scaled y-axis, THEN `get_ylim` SHALL return those two endpoints in the
   same decreasing order (the axis SHALL be inverted), not reordered into
   ascending order.
3. WHEN `set_xlim`/`set_ylim` is called with two endpoints in increasing order,
   THEN the committed view interval SHALL be ascending and `get_xlim`/`get_ylim`
   SHALL return them in increasing order.
4. The committed pair of endpoints SHALL have exactly the two magnitudes
   produced by applying the locator's singularity-avoiding normalizer and then
   the scale-domain restriction to the requested endpoints; the direction
   handling SHALL change only the order of that pair, never the values.
5. WHEN `set_xlim3d`/`set_ylim3d`/`set_zlim3d` on a 3-D axes is called with two
   endpoints in decreasing order, THEN the corresponding committed view interval
   SHALL be descending in the same way, preserving the requested inverted
   direction for that dimension on any scale.

## Requirement 2: The locator's singularity-avoiding normalizer returns endpoints in increasing order

**User story:** As a maintainer, I want the axis locator's singularity-avoiding
step to normalize a range without depending on the caller's requested
direction, so that the limit-setter alone is responsible for restoring the
requested direction and inversion works consistently across scales.

**Acceptance criteria**

1. WHEN a locator's `nonsingular(v0, v1)` method (the base `Locator.nonsingular`
   used by log and other default locators) is invoked with two finite endpoints,
   THEN it SHALL return the two endpoints in increasing order (the smaller value
   first), regardless of the order in which they were passed; in particular a
   descending pair SHALL be returned reordered into ascending order.
2. WHEN `nonsingular` receives a non-degenerate range (its two endpoints already
   sufficiently far apart), THEN it SHALL return exactly those two endpoint
   magnitudes, sorted into increasing order.
3. WHEN `nonsingular` receives a degenerate range (both endpoints equal or the
   interval too small relative to the endpoints' magnitude), THEN it SHALL
   expand the range so the two returned endpoints are distinct and in increasing
   order.
4. WHEN `nonsingular` receives non-finite input (an infinite or NaN endpoint) or
   an interval indistinguishable from zero, THEN it SHALL return the same
   fallback expanded range it produced before this change, so existing
   degenerate-range and autoscaling behavior is unaffected.
5. WHEN a limit-setter normalizes a descending request via `nonsingular` (which
   returns the pair ascending), THEN the limit-setter SHALL restore the
   caller's requested descending order afterward, so that the caller-visible
   inversion does not depend on `nonsingular` preserving order.

## Requirement 3: Preserve all existing limit-setting behavior

**User story:** As a user relying on matplotlib's established limit-setting
rules, I want every prior behavior of the limit-setters to keep working
unchanged, so that only the direction-preservation bug is fixed.

**Acceptance criteria**

1. The system SHALL keep expanding a degenerate range in which the two requested
   endpoints are equal, emitting the existing "identical … results in singular
   transformations; automatically expanding" warning and committing a
   non-empty interval.
2. IF a non-positive limit is requested on a log-scaled axis, THEN the
   limit-setter SHALL continue to warn and ignore that invalid limit (retaining
   the previous limit for that endpoint), exactly as before.
3. WHEN a limit is passed as `None`, THEN the limit-setter SHALL continue to
   reuse the axis's current corresponding limit for that endpoint.
4. WHEN limits are set on an axis that is shared with other axes and emission is
   enabled, THEN the limit-setter SHALL continue to propagate the committed
   interval to the shared sibling axes and to return the committed
   `(left, right)` / `(bottom, top)` pair.
5. WHEN an inverted range is committed and the axes are subsequently cleared and
   re-plotted, THEN the previously established inversion behavior of the axes
   SHALL continue to hold as it did before this change.
