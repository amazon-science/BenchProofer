# Requirements: `stackplot` must not mutate the Axes color cycle

## Introduction

The stacked-area plotting helper `matplotlib.stackplot.stackplot` (exposed to
users as `Axes.stackplot`) accepts an optional `colors` argument: a sequence of
color specifications used to color the successive stacked regions. In the
affected version, when `colors` is supplied, `stackplot` applies those colors by
calling `Axes.set_prop_cycle(color=colors)` on the parent Axes. This has two
undesirable consequences:

1. It **permanently reconfigures the Axes' property (color) cycle** as a side
   effect, so subsequent artists drawn on the same Axes no longer follow the
   original cycle. A user combining stacked plots with other plot types on one
   Axes cannot keep colors synchronized.
2. It routes the caller's colors through the property-cycle validator, which
   **rejects color-cycle reference tokens of the form `C<N>`** (e.g. `C0`,
   `C1`), raising a `ValueError`, even though those tokens are valid colors for
   `Axes.plot` and for patches.

The goal is to color the stacked regions directly from the supplied palette —
cycling through it with wrap-around — without ever mutating the Axes property
cycle, and while accepting every color token the general color resolver accepts
(including `C<N>` references). When no palette is supplied, the existing
behavior of drawing colors from the Axes property cycle must be preserved.

The affected code is the region-coloring logic inside
`lib/matplotlib/stackplot.py::stackplot`; the previously used entry point
`Axes.set_prop_cycle` and the per-region color source
`Axes._get_lines.get_next_color()` are the relevant collaborating APIs.

## Requirement 1: Supplying a color palette must not alter the Axes property cycle

**User story:** As a user producing multiple plot types on one Axes, I want
`stackplot` with an explicit `colors` argument to leave the Axes' color cycle
unchanged, so that colors stay synchronized across the other artists I draw on
the same Axes.

**Acceptance criteria**
1. WHEN `stackplot` is called with a non-`None` `colors` argument, THEN
   `stackplot` SHALL NOT modify the parent Axes' property (color) cycle.
2. WHEN a caller records the Axes' next cycle color before calling `stackplot`
   with an explicit `colors` argument, THEN the Axes SHALL yield that same next
   cycle color to the following artist drawn on that Axes after `stackplot`
   returns.
3. The system SHALL color the stacked regions directly from the supplied
   palette rather than by reconfiguring the Axes property cycle.

## Requirement 2: Color-cycle reference tokens (`C<N>`) must be accepted

**User story:** As a user, I want to pass `C<N>` color-cycle reference tokens
(e.g. `C0`, `C1`, `C2`) in the `colors` argument, so that stacked areas can
reuse the same palette references that `Axes.plot` and patches accept.

**Acceptance criteria**
1. WHEN `stackplot` is called with a `colors` sequence that contains one or more
   `C<N>` reference tokens, THEN `stackplot` SHALL complete successfully without
   raising `ValueError`.
2. WHEN `stackplot` is given a palette containing `C<N>` tokens, THEN each such
   token SHALL be applied as the facecolor of its region and resolved to the
   same color that the token denotes elsewhere in matplotlib.
3. The system SHALL NOT reject any color specification in `colors` that the
   general matplotlib color resolver would otherwise accept.

## Requirement 3: Regions are colored by cycling through the palette in order with wrap-around

**User story:** As a user, I want the supplied colors applied to the stacked
regions in order, wrapping around when there are more regions than colors, so
that coloring is predictable regardless of palette length.

**Acceptance criteria**
1. WHEN `stackplot` draws `n` stacked regions with an explicit non-empty
   `colors` palette, THEN region `i` (counting from 0) SHALL be assigned the
   facecolor at palette position `i mod len(colors)`.
2. WHEN the number of regions exceeds the palette length, THEN `stackplot`
   SHALL continue assigning colors by repeating the palette from its beginning,
   and SHALL still produce exactly one region per data series.
3. WHEN the palette contains at least as many colors as regions, THEN each
   region `i` SHALL be assigned exactly `colors[i]` and no palette entry beyond
   the region count SHALL be consulted.

## Requirement 4: The Axes property cycle is used only when no palette is supplied

**User story:** As a user who does not pass `colors`, I want stacked regions to
be colored from the Axes property cycle exactly as before, so that default
coloring behavior is unchanged.

**Acceptance criteria**
1. IF the `colors` argument is `None` (unspecified), THEN `stackplot` SHALL
   color each successive region by drawing the next color from the Axes
   property cycle.
2. WHEN `colors` is `None`, THEN `stackplot` SHALL advance the Axes property
   cycle by exactly one color per drawn region.
3. The system SHALL draw exactly `n` colors from the Axes property cycle when
   coloring `n` regions with no explicit palette.

## Requirement 5: Existing stackplot outputs and options are preserved

**User story:** As an existing user, I want all other `stackplot` behavior —
return value, labels, baselines, and data-key resolution — to remain unchanged,
so that the color-cycle fix introduces no regressions.

**Acceptance criteria**
1. WHEN `stackplot` succeeds, THEN it SHALL return a list of the filled-region
   artists with exactly one entry per stacked data series, in series order.
2. The system SHALL keep applying the `labels` sequence to the successive
   regions in order, applying no label once the sequence is exhausted.
3. The system SHALL keep supporting the `baseline` options `'zero'`, `'sym'`,
   `'wiggle'`, and `'weighted_wiggle'`, computing region boundaries as before,
   and SHALL keep rejecting any other `baseline` value.
4. The system SHALL keep resolving `x` and the `y` series from a `data`-mapping
   argument when data keys are passed as the positional arguments.
5. WHEN `baseline` is `'zero'`, THEN `stackplot` SHALL keep the first region's
   lower edge pinned as a sticky edge at zero.
6. The system SHALL keep forwarding any additional keyword arguments to the
   underlying filled-region drawing call unchanged.
