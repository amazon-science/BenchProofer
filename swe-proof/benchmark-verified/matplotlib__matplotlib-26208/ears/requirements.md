# Requirements — matplotlib twin-axis unit inheritance

## Introduction

In Matplotlib, `matplotlib.axes.Axes.twinx()` creates a second Axes that shares
the original Axes' x-axis (an independent y-axis on the right), and
`matplotlib.axes.Axes.twiny()` creates a second Axes that shares the original
Axes' y-axis (an independent x-axis on the top). The shared coordinate axis is
meant to be a faithful twin of the original coordinate axis.

Each coordinate axis (`Axis`) carries a per-axis unit/conversion setting exposed
as its `units` attribute (`ax.xaxis.units` / `ax.yaxis.units`). This setting
records how raw data values on that coordinate are interpreted and converted
(for example, when categorical/string data or date data has been plotted, a
converter and its unit state are established on that axis). When two Axes share a
coordinate, they must interpret that coordinate identically.

The affected code is `Axes.twinx` and `Axes.twiny` in
`lib/matplotlib/axes/_base.py`. The defect: the newly created twin Axes did not
receive the unit/conversion setting of the shared coordinate from the source
Axes. Because the twin's shared coordinate started with no unit setting, plotting
data whose interpretation depends on that setting could recompute limits with a
different (or absent) converter, which corrupted the source Axes' data limits
(they were replaced by `±inf`). The goal is that the twin Axes inherits, on its
shared coordinate, the exact unit/conversion setting of the source Axes so both
Axes interpret the shared coordinate identically and the source Axes' data limits
are preserved.

## Requirement 1: twinx inherits the shared x-coordinate's unit setting

**User story:** As a user creating a second y-axis with `twinx()`, I want the new
Axes to interpret the shared x-coordinate exactly as the original Axes does, so
that plotting on either Axes does not corrupt the shared coordinate's conversion
state or the original Axes' data limits.

**Acceptance criteria**

1. WHEN `Axes.twinx()` returns a new twin Axes, THEN the twin's x-axis unit
   setting (`ax2.xaxis.units`) SHALL be the same object as the source Axes'
   x-axis unit setting (`self.xaxis.units`).
2. IF the source Axes' x-axis has a non-`None` unit setting at the moment
   `twinx()` is called, THEN the returned twin's x-axis unit setting SHALL also
   be non-`None`.
3. IF the source Axes' x-axis unit setting is `None` at the moment `twinx()` is
   called, THEN the returned twin's x-axis unit setting SHALL be `None`.
4. The system SHALL copy the source's x-axis unit setting onto the twin so that a
   later plotting call on the twin uses the same coordinate interpretation as the
   source, leaving the source Axes' existing data limits unchanged (in
   particular, not replaced by infinite values).

## Requirement 2: twiny inherits the shared y-coordinate's unit setting

**User story:** As a user creating a second x-axis with `twiny()`, I want the new
Axes to interpret the shared y-coordinate exactly as the original Axes does, so
that plotting on either Axes does not corrupt the shared coordinate's conversion
state or the original Axes' data limits.

**Acceptance criteria**

1. WHEN `Axes.twiny()` returns a new twin Axes, THEN the twin's y-axis unit
   setting (`ax2.yaxis.units`) SHALL be the same object as the source Axes'
   y-axis unit setting (`self.yaxis.units`).
2. IF the source Axes' y-axis has a non-`None` unit setting at the moment
   `twiny()` is called, THEN the returned twin's y-axis unit setting SHALL also
   be non-`None`.
3. IF the source Axes' y-axis unit setting is `None` at the moment `twiny()` is
   called, THEN the returned twin's y-axis unit setting SHALL be `None`.
4. The system SHALL copy the source's y-axis unit setting onto the twin so that a
   later plotting call on the twin uses the same coordinate interpretation as the
   source, leaving the source Axes' existing data limits unchanged (in
   particular, not replaced by infinite values).

## Requirement 3: preserve existing twin-axis construction behavior

**User story:** As a user relying on the established behavior of `twinx()` and
`twiny()`, I want all their existing construction guarantees to remain intact, so
that adding unit inheritance does not regress any other aspect of twin Axes.

**Acceptance criteria**

1. The system SHALL continue to have `twinx()` return a new Axes that shares the
   source Axes' x-axis and that has an independent y-axis positioned opposite to
   the source's (on the right).
2. The system SHALL continue to have `twiny()` return a new Axes that shares the
   source Axes' y-axis and that has an independent x-axis positioned opposite to
   the source's (on the top).
3. WHEN `twinx()` creates the twin, THEN the twin's x-axis autoscale setting
   SHALL be inherited from the source Axes, and WHEN `twiny()` creates the twin,
   THEN the twin's y-axis autoscale setting SHALL be inherited from the source
   Axes.
4. The system SHALL keep the twin Axes' patch invisible and keep the twin's
   shared (invisible) coordinate axis hidden, matching the prior behavior of
   these two functions.
5. The unit-setting inheritance added for the shared coordinate SHALL NOT alter
   the source Axes' own axes, artists, or data limits as a side effect of
   creating the twin.
