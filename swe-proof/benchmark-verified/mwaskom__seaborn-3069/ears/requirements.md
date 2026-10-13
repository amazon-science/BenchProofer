# Requirements: Nominal scale axes should be drawn like categorical axes

## Introduction

In seaborn's objects interface (`seaborn._core.plot`), the `Plot` object renders
each subplot through the internal `Plotter` class. When a plot is displayed, the
`Plotter._finalize_figure` method performs per-axis finalization such as applying
user-specified axis limits.

Seaborn's classic categorical plots give their category axis a distinctive
treatment that the objects interface does not yet reproduce for nominal
(categorical) scales:

1. the axis extent runs half a unit beyond the first and last category position,
   instead of using matplotlib's ordinary data-margin logic;
2. the axis grid is not drawn, even when the active style would otherwise draw
   one;
3. on the vertical (`y`) axis the extent is reversed, so categories read from top
   to bottom.

The goal is to make axes that carry a nominal scale (`seaborn._core.scales.Nominal`),
including inferred nominal scales, receive this same treatment at
finalization time, while leaving numeric/continuous axes and any explicitly
requested limits untouched. This behavior belongs in `Plotter._finalize_figure`,
using the plotter's resolved scales for each axis and matplotlib's axis object
(`ax.xaxis` / `ax.yaxis`).

Throughout this document, "nominal axis" means an axis whose resolved scale is a
`Nominal` scale, and `nticks` means the number of major tick marks present on
that axis after the categories have been laid out.

## Requirement 1: Pin the extent of a nominal axis to the categorical range

**User story:** As a user plotting categorical data with the objects interface,
I want a nominal axis to span exactly the category positions plus a half-unit
pad, so that my categorical plot matches the appearance of seaborn's classic
categorical plots and the outermost categories are not clipped or floated by
default margins.

**Acceptance criteria**

1. WHEN a subplot is finalized and a given axis carries a nominal scale and the
   user has not pinned an explicit limit on that axis, THEN the plotter SHALL set
   that axis's limits so that the lower bound is `-0.5` and the upper bound is
   `nticks - 0.5`, where `nticks` is the number of major tick marks on that axis.
2. WHEN the nominal axis being pinned is a horizontal (`x`) axis, THEN the
   resulting axis limits SHALL be `(-0.5, nticks - 0.5)` in that order.
3. WHEN the nominal axis being pinned is a vertical (`y`) axis, THEN the resulting
   axis limits SHALL be reversed to `(nticks - 0.5, -0.5)`, so that the first
   category appears at the top and the last at the bottom.
4. The system SHALL derive `nticks` from the axis's own major tick marks at
   finalization time, so that a nominal `x` axis with three categories is pinned
   to `(-0.5, 2.5)` and a nominal `y` axis with three categories is pinned to
   `(2.5, -0.5)`.
5. WHEN this categorical extent is applied, THEN the plotter SHALL suppress
   matplotlib's automatic re-margining of that axis so that the pinned bounds are
   the final displayed limits.

## Requirement 2: Hide the grid on a nominal axis

**User story:** As a user plotting categorical data, I want the grid lines along
a nominal axis to be hidden, so that the categorical axis looks like seaborn's
classic categorical plots regardless of the active style's grid setting.

**Acceptance criteria**

1. WHEN a subplot is finalized and a given axis carries a nominal scale, THEN the
   plotter SHALL disable the grid lines associated with that axis.
2. WHILE an axis carries a nominal scale, the plotter SHALL hide that axis's grid
   lines even when the active theme/style would otherwise show them, such that
   none of that axis's grid lines are visible.
3. IF an axis carries a nominal scale, THEN the grid SHALL be hidden regardless of
   whether the user has pinned an explicit limit on that axis.

## Requirement 3: Respect user-specified limits on a nominal axis

**User story:** As a user who pins explicit limits on a categorical axis, I want
my limits to be honored, so that I retain control over the axis range even when
the categorical treatment is otherwise active.

**Acceptance criteria**

1. IF the user has pinned an explicit limit on a nominal axis, THEN the plotter
   SHALL NOT override that axis's limits with the categorical `(-0.5, nticks - 0.5)`
   extent, and the axis's final limits SHALL equal the user-specified limits.
2. WHEN a user pins an explicit lower/upper bound pair on a nominal `x` axis,
   THEN the final `x` limits SHALL be exactly that user-specified pair, in the
   order the user gave, and SHALL NOT be replaced by the categorical
   `(-0.5, nticks - 0.5)` extent.
3. WHEN a user pins an explicit lower/upper bound pair on a nominal `y` axis,
   THEN the final `y` limits SHALL be exactly that user-specified pair, in the
   order the user gave (i.e. NOT reversed the way an unpinned nominal `y` axis
   would be), and SHALL NOT be replaced by the categorical extent.

## Requirement 4: Leave non-nominal axes and unrelated behavior unchanged

**User story:** As a user of the objects interface, I want numeric and other
non-categorical axes to keep behaving exactly as before, so that adding the
nominal treatment does not regress existing plots.

**Acceptance criteria**

1. IF an axis does not carry a nominal scale, THEN the plotter SHALL NOT pin the
   categorical extent on that axis and SHALL NOT hide that axis's grid.
2. The system SHALL continue to apply user-specified axis limits during
   finalization for all axes, including converting string category bounds to
   padded numeric positions, exactly as before this change.
3. The system SHALL preserve all existing `Plot` construction, faceting, pairing,
   axis-sharing, labeling, theming, layout-engine, and saving/rendering behavior
   unchanged by this modification.
4. The system SHALL keep producing a valid matplotlib figure whose subplots and
   axes are created and finalized without error for plots that use numeric,
   faceted, paired, or log-scaled axes.
