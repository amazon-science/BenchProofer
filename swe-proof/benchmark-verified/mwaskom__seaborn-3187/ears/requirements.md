# Legend labels for large-magnitude numeric variables

## Introduction

Seaborn builds legends for numeric semantic variables (e.g. `color`, `hue`,
`pointsize`, `size`) by generating tick locations for the variable's range and
formatting them into human-readable text labels. Two code paths do this:

- The objects interface: `Continuous._setup` in `seaborn/_core/scales.py`,
  which produces the `(locations, labels)` pair stored on the scale for legend
  rendering.
- The classic relational interface (`relplot`, `scatterplot`, `lineplot`):
  `locator_to_legend_entries` in `seaborn/utils.py`, which returns the numeric
  levels and their formatted labels for brief numeric legends.

Both paths format tick values with matplotlib's `ScalarFormatter`. When the
underlying values are large in magnitude, that formatter by default factors out
a shared multiplicative/additive *offset* (and may switch to scientific
notation), emitting small tick strings such as `"0.0"`, `"0.5"`, `"1.0"`
alongside a separate offset annotation. Seaborn's legend has no place to display
that offset annotation, so the printed legend labels are numerically wrong —
they appear to be near zero instead of near the true large values.

The goal is to ensure the formatted legend labels always represent the true
magnitude of the data, with no reliance on a separate, undisplayed offset or
scientific-notation factor.

## Requirement 1: Legend labels reflect true magnitude for large numeric ranges (objects interface)

**User story:** As a user plotting a numeric variable with large values through
the objects interface, I want the legend labels to show the actual data
magnitudes, so that the legend is not misleadingly close to zero.

**Acceptance criteria**

1. WHEN a `Continuous` scale builds its legend entries for a numeric property,
   THEN the tick label formatter SHALL be configured so that no shared offset
   is factored out of the tick labels (offset display disabled).
2. WHEN a `Continuous` scale builds its legend entries for a numeric property,
   THEN the tick label formatter SHALL be configured so that scientific
   notation is not used to factor out a common power of ten from the tick
   labels (scientific mode disabled).
3. WHEN the mapped numeric values are large enough that the default formatter
   would otherwise factor out a shared offset or common power of ten, THEN each
   generated legend label string SHALL represent the true magnitude of its
   corresponding tick value, rather than a small residual that relies on a
   separate, undisplayed offset factor.
4. IF the formatter object in use does not expose the ability to disable an
   offset or scientific notation, THEN the scale SHALL still produce its legend
   entries without error, applying the disabling only where the formatter
   supports it.
5. The generated legend SHALL retain one label per retained tick location, so
   that locations and labels remain paired one-to-one.

## Requirement 2: Legend labels reflect true magnitude for large numeric ranges (relational interface)

**User story:** As a user calling `relplot`, `scatterplot`, or `lineplot` with a
numeric hue/size mapping over large values, I want the legend labels to show the
actual data magnitudes, so that the legend is correct.

**Acceptance criteria**

1. WHEN `locator_to_legend_entries` formats numeric levels using a non-log
   (scalar) formatter, THEN that formatter SHALL be configured so that no shared
   offset is factored out of the labels (offset display disabled).
2. WHEN `locator_to_legend_entries` formats numeric levels using a non-log
   (scalar) formatter, THEN that formatter SHALL be configured so that
   scientific notation is not used to factor out a common power of ten
   (scientific mode disabled).
3. WHEN the numeric levels are large enough that the default formatter would
   otherwise factor out a shared offset or common power of ten, THEN each
   returned formatted label string SHALL represent the true magnitude of its
   corresponding level, rather than a small residual that relies on a separate,
   undisplayed offset factor.
4. The returned numeric levels and their formatted labels SHALL remain in
   one-to-one correspondence and cover the same in-range levels as before.

## Requirement 3: Preserve existing legend and plotting behavior

**User story:** As a maintainer, I want the fix to change only the magnitude
representation of large-value legends, so that all existing legend, scaling, and
plotting behavior continues to work.

**Acceptance criteria**

1. WHEN numeric variables of ordinary (small) magnitude are mapped, THEN the
   generated legend labels SHALL continue to be the same human-readable numeric
   strings as before, with no regression in formatting.
2. The system SHALL continue to produce legends for numeric, categorical, and
   log-scaled semantic variables through both the objects and relational
   interfaces exactly as before, aside from the corrected large-magnitude
   labels.
3. The system SHALL continue to support suppression of legends where a mark or
   scale opts out, and SHALL not create a legend where none was previously
   created.
4. WHEN a log scale is in use for a numeric legend, THEN the existing
   log-appropriate label formatting SHALL be preserved and unaffected by the
   offset/scientific-notation handling.
