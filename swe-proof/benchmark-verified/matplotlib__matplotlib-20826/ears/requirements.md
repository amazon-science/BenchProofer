# Requirements: `ax.clear()` must not un-hide shared-axis ticks and tick labels

## Introduction

When axes are created with shared x or y axes (for example via
`pyplot.subplots(..., sharex=True, sharey=True)`), matplotlib suppresses the
per-side ticks and tick labels of interior subplots so that only the outer
subplots show them. This suppression is recorded as per-side visibility
settings in the axis' tick-keyword tables.

Regression: calling `Axes.clear()` (equivalently `ax.cla()`) re-initialises
each axis through `matplotlib.axis.Axis.clear`, which in turn rebuilds the
major and minor tick-keyword tables. In the affected version this
re-initialisation discards ALL previously recorded per-tick settings and keeps
only freshly recomputed defaults. As a consequence, the per-side tick and
tick-label visibility settings that had hidden interior ticks/labels are lost:
after `clear()`, ticks and tick labels that should stay hidden reappear
(including extra ticks on the top/right sides), even though the axes remain
linked. This is a behavior change from the previous release.

The affected code is `matplotlib.axis.Axis.clear` and its tick-keyword-table
re-initialisation helpers (`_reset_major_tick_kw` / `_reset_minor_tick_kw`),
which maintain the `_major_tick_kw` and `_minor_tick_kw` tables consumed when
new `Tick` objects are created (`reset_ticks`). The goal is to make `clear()`
recompute only the grid-visibility flag while preserving every other
previously-recorded tick-keyword entry, so that shared-axis visibility survives
a clear.

## Requirement 1: Preserve recorded tick-keyword settings across a clear

**User story:** As a user who clears and re-draws axes (e.g. per animation
frame), I want `ax.clear()` to keep the tick and tick-label visibility that was
configured for the axes, so that clearing does not silently re-expose ticks and
labels that were meant to stay hidden.

**Acceptance criteria**

1. WHEN `matplotlib.axis.Axis.clear` re-initialises an axis whose major or
   minor tick-keyword table already holds entries other than the
   grid-visibility flag (for example per-side tick-visibility or
   tick-label-visibility flags), THEN `Axis.clear` SHALL retain every such
   entry with its existing value in the corresponding table after the clear.
2. WHEN `matplotlib.axis.Axis.clear` re-initialises an axis, THEN it SHALL NOT
   remove, drop, or reset to a default any per-side tick or tick-label
   visibility setting that was present before the clear, except for the
   grid-visibility flag governed by Requirement 2.
3. The system SHALL confine this re-initialisation of tick-keyword state to the
   clear path (`Axis.clear`), so that a `clear()` no longer relies on the
   settings applied at axes construction time to restore per-side visibility.
4. WHEN a shared-axis group has interior ticks and tick labels suppressed and
   one of its axes is cleared via `Axes.clear` / `ax.cla()`, THEN the cleared
   axes SHALL continue to suppress those interior ticks and tick labels (i.e.
   the rendered result SHALL match an equivalent axes that was never cleared).

## Requirement 2: Recompute the grid-visibility flag from current preferences

**User story:** As a user, I want a cleared axis to reflect the current global
grid preferences, so that grid-on/grid-off behavior after `clear()` matches a
freshly created axis.

**Acceptance criteria**

1. WHEN `matplotlib.axis.Axis.clear` re-initialises the major tick-keyword
   table, THEN it SHALL set that table's grid-visibility flag to true if and
   only if the global grid preference (`axes.grid`) is enabled AND the global
   grid-selection preference (`axes.grid.which`) is either the combined
   selection or the major selection; otherwise it SHALL set the flag to false.
2. WHEN `matplotlib.axis.Axis.clear` re-initialises the minor tick-keyword
   table, THEN it SHALL set that table's grid-visibility flag to true if and
   only if the global grid preference (`axes.grid`) is enabled AND the global
   grid-selection preference (`axes.grid.which`) is either the combined
   selection or the minor selection; otherwise it SHALL set the flag to false.
3. The system SHALL compute each table's grid-visibility flag solely from the
   current values of those two global preferences, independent of any prior
   value of the grid-visibility flag.
4. WHEN new `Tick` objects are subsequently created for the axis after a clear
   (`reset_ticks`), THEN they SHALL inherit the tick-keyword state as
   determined by Requirements 1 and 2 (recomputed grid flag, all other entries
   preserved).

## Requirement 3: Preserve existing reset and configuration behavior

**User story:** As a maintainer, I want the fix to leave the rest of the
clear/reset and tick-configuration behavior intact, so that existing grid,
tick-parameter, and shared-axes workflows keep working.

**Acceptance criteria**

1. The system SHALL keep the full-reset semantics of
   `Axis.set_tick_params(..., reset=True)`: when a reset is requested, the
   targeted tick-keyword table(s) SHALL be re-initialised to only the recomputed
   grid-visibility flag before the supplied keyword updates are applied.
2. WHEN `Axes.clear()` is applied to axes that share an x or y axis with
   another axes, THEN the axes SHALL remain joined in the same shared group and
   SHALL keep matching view limits and scale with that group.
3. The system SHALL keep grid rendering after a clear consistent with the
   global grid preferences, including the combined / major-only / minor-only
   selection cases and explicit `grid()` toggling.
4. The system SHALL keep tick and tick-label appearance configuration via
   `tick_params` / `set_tick_params` working after a clear, including
   re-applying tick parameters to newly created ticks.
5. WHEN clearing twinned axes (`twinx` / `twiny`) or axes with inverted limits,
   THEN `clear()` SHALL preserve the previously working behavior for those axes
   (twin relationships and inversion handling) unchanged.
6. WHEN re-ticking or updating tick labels on shared axes after plotting,
   THEN the previously working tick-label update behavior SHALL be preserved.
