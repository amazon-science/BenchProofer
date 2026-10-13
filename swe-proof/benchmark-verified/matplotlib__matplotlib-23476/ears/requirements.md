# Requirements: Stable figure resolution across pickle round-trips

## Introduction

`matplotlib.figure.Figure` supports being serialized with the standard `pickle`
protocol. Serialization is driven by `Figure.__getstate__`, which builds the
dictionary of instance state that pickle stores, and `Figure.__setstate__`,
which restores it.

A figure's working resolution (its dots-per-inch, exposed as the `Figure.dpi`
property and stored internally on the `_dpi` attribute) can be temporarily
scaled to match a high-density display surface. When a canvas is first attached
to a figure (`FigureCanvasBase.__init__` in `matplotlib.backend_bases`), the
figure's resolution at that moment is recorded as a baseline on the
`_original_dpi` attribute. A subsequent device-pixel-ratio change
(`FigureCanvasBase._set_device_pixel_ratio`) rescales the working resolution to
`ratio * baseline` via `Figure._set_dpi`.

Because the *scaled* working resolution was the value captured for pickling,
every save/restore cycle re-applied the scaling: the restored figure attached a
fresh canvas, re-recorded the (already scaled) resolution as its new baseline,
and the next cycle scaled again. The resolution therefore doubled (or otherwise
grew) on each round trip, eventually raising an `OverflowError` on affected
backends (observed on high-DPI displays such as Apple M1 Macs).

The goal is to make a figure's resolution invariant under pickling: serializing
and then deserializing a figure must yield the unscaled baseline resolution,
regardless of any device-pixel-ratio scaling that was applied to the live
figure, so that repeated round-trips are stable.

## Requirement 1: Serialize the unscaled baseline resolution

**User story:** As a user who saves and reloads figures, I want a pickled
figure to remember its original resolution rather than a display-scaled one, so
that reloading it does not change its dpi and repeated save/load cycles do not
inflate it.

**Acceptance criteria**

1. WHEN a figure's serialized state is produced by `Figure.__getstate__` and the
   figure carries a recorded baseline resolution (`_original_dpi`), THEN
   `Figure.__getstate__` SHALL record that baseline resolution as the figure's
   resolution (`_dpi`) in the serialized state, in place of the figure's current
   working resolution.
2. WHEN a figure's serialized state is produced by `Figure.__getstate__` and the
   figure carries no recorded baseline resolution, THEN `Figure.__getstate__`
   SHALL record the figure's current working resolution as its resolution in the
   serialized state, leaving that value unchanged.
3. WHEN a figure whose working resolution has been scaled away from its baseline
   by a device-pixel-ratio change is pickled and then unpickled, THEN the
   restored figure's `dpi` SHALL equal the baseline resolution that was in
   effect before the device-pixel-ratio scaling, not the scaled value.
4. WHEN a figure is pickled and unpickled repeatedly in succession, THEN the
   restored figure's `dpi` SHALL remain constant across every cycle and SHALL
   NOT grow from one cycle to the next.
5. The system SHALL determine the recorded resolution by selecting the baseline
   resolution when one is present and otherwise the current working resolution;
   it SHALL NOT compute the recorded value by any arithmetic on the two
   resolutions.

## Requirement 2: Preserve unrelated figure state and existing resolution behavior

**User story:** As a maintainer, I want the resolution fix to leave all other
figure and resolution behavior untouched, so that no existing functionality
regresses.

**Acceptance criteria**

1. WHEN `Figure.__getstate__` produces serialized state, THEN it SHALL continue
   to exclude the non-picklable canvas and cached renderer from that state and
   SHALL continue to include the recorded library version, exactly as before.
2. WHEN a figure that has never had its resolution scaled is pickled and
   unpickled, THEN the restored figure's `dpi` SHALL equal the figure's
   resolution at the time it was pickled.
3. WHEN a figure's resolution is changed directly through the `Figure.dpi`
   property (or `Figure._set_dpi`), THEN the figure's reported `dpi`, its
   dpi-scale transform, and its pixel size SHALL update consistently as they did
   before this change.
4. WHEN a canvas applies a device-pixel-ratio change to a live (non-pickled)
   figure, THEN the figure's working resolution SHALL still become the product
   of that ratio and the recorded baseline resolution.
5. IF a saved figure was produced by a different library version than the one
   loading it, THEN `Figure.__setstate__` SHALL still emit the existing
   version-mismatch warning and otherwise restore the figure.
6. The system SHALL keep `Figure` picklable and `Figure` deep-copyable with no
   loss of previously preserved state.
