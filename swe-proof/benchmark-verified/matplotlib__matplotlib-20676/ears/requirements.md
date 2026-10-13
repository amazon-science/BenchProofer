# Requirements: Interactive SpanSelector must not alter the host axes' view limits

## Introduction

`matplotlib.widgets.SpanSelector` (in `lib/matplotlib/widgets.py`) lets a user
drag out a min/max range along one axis of an `Axes`. When constructed with
`interactive=True` (the successor to the deprecated `span_stays`), it draws a
pair of movable edge handles at the two ends of the current span. These handles
are `ToolLineHandles`, which for a `'horizontal'` selector are vertical lines
created with `Axes.axvline` and for a `'vertical'` selector are horizontal lines
created with `Axes.axhline`.

At construction time the selector has no active span: its internal rectangle
sits at the origin with zero width/height, so its `extents` are effectively
`(0, 0)`. The edge handles were previously initialized from those extents, i.e.
at coordinate `0`. Because `axvline`/`axhline` are data artists that participate
in autoscaling/data-limit bookkeeping, placing a handle at `0` forced the axis'
view interval to grow to include `0`. As reported, constructing
`SpanSelector(ax, print, "horizontal", interactive=True)` on data spanning
`(10, 20)` expanded the lower x-limit down to `0` — before the user interacted
with the widget at all. In Matplotlib 3.4 this did not happen.

The goal is: creating an interactive `SpanSelector` must leave the axes' view
bounds exactly as they were, while the edge handles are still created and remain
fully functional (they must track the span as the user presses and drags). The
fix seeds the initial handle positions from the axis' current bounds
(`Axes.get_xbound` for a horizontal selector, `Axes.get_ybound` for a vertical
one) instead of from the empty span, so the handles start on the existing view
edges and therefore introduce no new data limit.

## Requirement 1: Constructing an interactive selector preserves the axes' view bounds

**User story:** As a user attaching an interactive `SpanSelector` to an existing
plot, I want my axes limits to stay exactly where they were, so that merely
creating the selector does not rescale or shift my view.

**Acceptance criteria**

1. WHEN a `SpanSelector` is constructed on an `Axes` with `interactive=True`,
   THEN the selector SHALL leave the axes' x view bounds (`Axes.get_xbound`)
   unchanged from their value immediately before construction.
2. WHEN a `SpanSelector` is constructed on an `Axes` with `interactive=True`,
   THEN the selector SHALL leave the axes' y view bounds (`Axes.get_ybound`)
   unchanged from their value immediately before construction.
3. The system SHALL NOT expand, contract, or shift either axis' view interval as
   a side effect of creating the interactive edge handles; in particular it SHALL
   NOT force the view interval to include the coordinate `0`.

## Requirement 2: Initial edge-handle positions are seeded from the axis bounds

**User story:** As a maintainer, I want the interactive edge handles to be placed
on the current view edges at creation time, so that they are drawn without
introducing any new data extent.

**Acceptance criteria**

1. WHEN an interactive `SpanSelector` sets up its edge handles, THEN it SHALL
   position the two handles at the current bounds of the axis along which it
   operates: the x bounds (`Axes.get_xbound`) for a `'horizontal'` selector and
   the y bounds (`Axes.get_ybound`) for a `'vertical'` selector.
2. WHEN an interactive `SpanSelector` has just been constructed and has not yet
   been interacted with, THEN its edge handles' reported positions SHALL equal
   the two-element list of the operating axis' bounds — the x bounds for a
   `'horizontal'` selector and the y bounds for a `'vertical'` selector.
3. The system SHALL derive the initial handle positions from the axis' existing
   bounds rather than from the selector's (empty) span extents, so that handle
   creation adds no coordinate outside the current view.

## Requirement 3: Interaction still drives the span and preserves the view bounds

**User story:** As a user, I want pressing and dragging to define a selection and
move the edge handles just as before, without the created widget having disturbed
my axes limits.

**Acceptance criteria**

1. WHEN the user presses at one coordinate and then moves to another coordinate
   on an interactive `SpanSelector`, THEN the two edge handles' reported
   positions SHALL become the span's endpoints along the operating axis: for a
   `'horizontal'` selector the handles SHALL report the press and move x
   coordinates, and for a `'vertical'` selector the press and move y coordinates.
2. WHILE the user presses and drags to create or resize a span, the selector
   SHALL keep the axes' x view bounds and y view bounds unchanged from their
   pre-construction values.
3. WHEN a span is defined interactively, THEN updating the span SHALL keep the
   edge handles synchronized with the current span extents.

## Requirement 4: Preserve existing SpanSelector behavior (regression protection)

**User story:** As a maintainer, I want all previously working `SpanSelector`
behavior to be unaffected by the handle-initialization change, so that
non-interactive use, span callbacks, dragging, and direction handling continue to
work.

**Acceptance criteria**

1. The system SHALL continue to create the interactive edge handles as line
   artists on the axes (vertical lines for a `'horizontal'` selector, horizontal
   lines for a `'vertical'` selector), so that both handles exist and are
   available for interaction after construction.
2. WHEN a user completes a selection whose span exceeds `minspan`, THEN the
   selector SHALL invoke its `onselect` callback with the span's minimum and
   maximum values, exactly as before.
3. WHEN a `SpanSelector` is used to drag or resize an existing span (including
   dragging from within the region when enabled), THEN the resulting span extents
   SHALL be computed as before and the reported `extents` SHALL reflect the moved
   or resized range.
4. WHEN the selector's `direction` is changed after construction, THEN the
   selector SHALL rebuild its rectangle and, if interactive, its edge handles for
   the new direction, and SHALL continue to operate along the newly selected
   axis.
5. The system SHALL continue to support both `'horizontal'` and `'vertical'`
   directions with identical semantics, differing only in which axis is used for
   the span, the rectangle orientation, and the handle line orientation.
