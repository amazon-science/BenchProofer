# Requirements: Offset (exponent) text color follows tick label color

## Introduction

In Matplotlib, when an axis uses scientific/offset notation, the shared
"offset text" (for example the `1e9` exponent multiplier shown at the end of
an axis) is drawn as a `Text` artist named `offsetText` on the axis. This
artist is created during axis initialization in `matplotlib.axis` — in the
`XAxis._init` method for the x-axis and the `YAxis._init` method for the
y-axis.

Matplotlib exposes two related runtime configuration parameters (rcParams) per
axis:

- `xtick.color` / `ytick.color` — the color of the tick marks.
- `xtick.labelcolor` / `ytick.labelcolor` — the color of the tick *labels*.
  These accept the special sentinel value `'inherit'`, meaning "use the
  corresponding tick color".

The defect: the offset text's color is chosen from the tick *mark* color
(`xtick.color` / `ytick.color`) even when a distinct tick *label* color has
been configured. Because the offset text is conceptually a label (it annotates
the axis scale, like the tick labels), its color should track the tick label
color configuration, honoring the `'inherit'` sentinel. This document
specifies the color that the offset text artist must receive when an axis is
initialized.

## Requirement 1: X-axis offset text honors tick label color

**User story:** As a user who styles axis tick labels via rcParams, I want the
x-axis offset/exponent text to take the same color as my tick labels, so that
all label-like text on the axis is visually consistent.

**Acceptance criteria**

1. WHEN a new x-axis is initialized while the x-axis tick label color
   configuration holds a concrete color value (any value other than the
   `'inherit'` sentinel), THEN the axis SHALL set the color of its offset text
   artist to that configured tick label color.
2. WHEN a new x-axis is initialized while the x-axis tick label color
   configuration holds the `'inherit'` sentinel value, THEN the axis SHALL set
   the color of its offset text artist to the configured x-axis tick (mark)
   color.
3. The system SHALL determine the x-axis offset text color solely from the
   x-axis tick label color and x-axis tick color configuration as described
   above, and SHALL NOT color the x-axis offset text from the tick color when
   a concrete tick label color is configured.

## Requirement 2: Y-axis offset text honors tick label color

**User story:** As a user who styles axis tick labels via rcParams, I want the
y-axis offset/exponent text to take the same color as my tick labels, so that
all label-like text on the axis is visually consistent.

**Acceptance criteria**

1. WHEN a new y-axis is initialized while the y-axis tick label color
   configuration holds a concrete color value (any value other than the
   `'inherit'` sentinel), THEN the axis SHALL set the color of its offset text
   artist to that configured tick label color.
2. WHEN a new y-axis is initialized while the y-axis tick label color
   configuration holds the `'inherit'` sentinel value, THEN the axis SHALL set
   the color of its offset text artist to the configured y-axis tick (mark)
   color.
3. The system SHALL determine the y-axis offset text color solely from the
   y-axis tick label color and y-axis tick color configuration as described
   above, and SHALL NOT color the y-axis offset text from the tick color when
   a concrete tick label color is configured.

## Requirement 3: Preserve existing offset text initialization behavior

**User story:** As a maintainer, I want the offset text color change to leave
every other aspect of axis initialization intact, so that no existing behavior
regresses.

**Acceptance criteria**

1. The system SHALL continue to create the offset text artist for both the
   x-axis and the y-axis during axis initialization, retrievable through the
   axis's public accessor for the offset text.
2. The system SHALL preserve the existing position, alignment, transform, and
   font-size configuration applied to the offset text artist for each axis
   (the offset text remains anchored at the far end of its axis as before).
3. WHEN neither tick label color parameter has been overridden away from the
   default configuration, THEN the offset text color for each axis SHALL match
   the color it had before this change (i.e., the default appearance is
   unchanged).
4. The system SHALL leave the color of tick marks and tick labels themselves
   unchanged; only the offset text color selection is affected.
