# Requirements: Concise date formatter must keep the year offset for sub-year, non-January spans

## Introduction

`matplotlib.dates.ConciseDateFormatter` (in `lib/matplotlib/dates.py`) formats
the tick labels of a date axis and, separately, produces an *offset* label — the
short summary string shown to the side of the axis (returned by
`ConciseDateFormatter.get_offset()`), which carries the coarse context (typically
the year) that is not repeated on every tick.

Its `format_ticks` method decides two things from the calendar breakdown of the
tick positions:

1. the *level* — which calendar component (year, month, day, hour, minute,
   second) is the finest one that actually varies across the ticks — and
2. whether to *display the offset* label, which by default carries the year.

The reported bug: when the plotted range spans less than a year and does **not**
include January, the month varies across ticks but the year is shown nowhere —
neither on the ticks (which show only months) nor in the offset (which was being
suppressed). The user therefore loses the year entirely. The offset was being
suppressed whenever the coarsest varying component was year or month, on the
assumption that a start-of-period tick would already display it; that assumption
is false when no start-of-year (January) tick is present.

The goal: suppress the offset only when a start-of-period tick genuinely carries
the coarse information, and otherwise keep the offset so the year remains visible.
This is a distinct defect from the earlier issue about the offset changing across
redraws, and must not reintroduce it.

## Requirement 1: Select the labelling level from the coarsest varying component

**User story:** As a user of a concise date axis, I want tick labels to describe
the finest calendar component that actually changes across the visible ticks, so
that labels are neither redundant nor missing detail.

**Acceptance criteria**

1. WHEN `format_ticks` is invoked with a set of tick date values, THEN the
   formatter SHALL derive, for each tick, the ordered calendar components
   year, month, day, hour, minute, second.
2. WHEN scanning the calendar components from finest (second) toward coarsest
   (year), THEN the formatter SHALL choose as the labelling level the first
   component whose values are not all identical across the ticks.
3. IF every component from year through second takes a single constant value
   across all ticks, THEN the formatter SHALL fall back to the finest
   (sub-second/second) level so that the ticks are still distinguished.
4. WHEN a varying component is found at a given level, THEN the formatter SHALL
   stop scanning at that level and use it, and SHALL NOT let a coarser (more
   significant) component override the chosen level.

## Requirement 2: Keep the offset unless a start-of-period tick already shows the coarse context

**User story:** As a user plotting a range shorter than a year that does not
begin in January, I want the year to appear in the offset label, so that the
plotted year is never lost from the figure.

**Acceptance criteria**

1. The offset label SHALL be displayed by default (subject to the formatter's
   configured offset-enable setting).
2. IF the chosen labelling level is a component coarser than day — that is, the
   year or the month is the finest varying component — AND the value `1`
   (i.e. January for the month component, or the first unit for the year
   component) occurs among that component's values across the ticks, THEN the
   formatter SHALL suppress the offset label, because a start-of-period tick
   already carries the coarse context.
3. IF the chosen labelling level is the year or the month AND the value `1` does
   **not** occur among that component's values across the ticks, THEN the
   formatter SHALL keep the offset label displayed, so that the coarse context
   (the year) remains visible even though no start-of-period tick is present.
4. WHEN the plotted range spans less than one year, includes more than one month,
   and does not include January, THEN `ConciseDateFormatter.get_offset()` SHALL
   return a non-empty string containing the year rather than an empty string.
5. IF the chosen labelling level is day or finer (day, hour, minute, second),
   THEN the formatter SHALL leave the offset display decision unchanged from its
   configured/default state and SHALL NOT suppress it on account of the level.

## Requirement 3: Preserve existing concise-offset behaviour (regression protection)

**User story:** As a maintainer, I want the previously correct offset behaviours
to remain intact, so that this fix does not regress other date ranges.

**Acceptance criteria**

1. WHEN the ticks include a January (month value `1`) start-of-year tick while
   months vary, THEN the formatter SHALL continue to suppress the offset label
   (the year already appears on that tick), matching the prior behaviour.
2. WHEN the formatter is constructed with the offset display disabled, THEN the
   formatter SHALL leave the offset label empty regardless of the level and
   value-`1` conditions.
3. The formatter SHALL keep producing the same offset string content for the
   previously supported ranges (single instant, sub-day, day, month-with-January,
   and multi-year spans), so that only the sub-year non-January case changes.
4. WHEN the offset label is displayed, THEN the formatter SHALL format it using
   the offset format string associated with the chosen level and SHALL return it
   through `get_offset()`; WHEN the offset label is suppressed, THEN `get_offset()`
   SHALL return an empty string.
5. The system SHALL leave tick-label formatting, level-dependent tick formats,
   and the seconds/microseconds trailing-zero handling otherwise unchanged.
