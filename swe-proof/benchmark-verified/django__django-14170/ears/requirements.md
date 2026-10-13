# Requirements: Correct year-range bounds for ISO week-numbering year lookups

## Introduction

Django's ORM lets a query filter on the *year component* of a date or datetime
column, either through the `__year` lookup (calendar year, via `ExtractYear`)
or the `__iso_year` lookup (ISO-8601 week-numbering year, via `ExtractIsoYear`
in `django/db/models/functions/datetime.py`). When such a lookup is compared
against a direct integer value, `YearLookup` (in
`django/db/models/lookups.py`) optimizes the query: instead of computing a
per-row `EXTRACT(...)` it rewrites the comparison into an inclusive `BETWEEN
lower AND upper` range test on the raw column, so an ordinary index on the
column can serve the query. The range bounds are produced by
`year_lookup_bounds_for_date_field` and `year_lookup_bounds_for_datetime_field`
on the database operations object (`django/db/backends/base/operations.py`).

The defect: this optimization computes its `[lower, upper]` bounds using
**calendar-year** boundaries (January 1st … December 31st) unconditionally,
even when the lookup is an ISO-year lookup (`__iso_year`, or a filter over an
explicit `ExtractIsoYear` annotation). Because an ISO week-numbering year does
not coincide with the calendar year (it may begin in late December of the prior
calendar year or in early January), applying calendar-year bounds to an
`iso_year` filter selects the wrong rows. Notably, using `ExtractIsoYear`
directly in an annotation produced the correct `EXTRACT('isoyear' ...)` SQL, so
the bug only surfaced through the filter/lookup path.

The goal is to make the year-range optimization produce ISO-year boundaries
when (and only when) the underlying lookup is an ISO-year extraction, while
leaving calendar-year behavior, the choice of column type, and all other
lookups unchanged.

## Requirement 1: ISO-year bounds for date columns

**User story:** As a developer filtering a `DateField` by ISO week-numbering
year, I want the range optimization to use ISO-year boundaries, so that the
filter returns exactly the rows whose ISO year equals the queried value.

**Acceptance criteria**

1. WHEN the range bounds for a date column are requested for ISO-year mode with
   an integer year `value`, THEN the operations object SHALL return a two-element
   `[lower, upper]` list whose lower bound is the first day of ISO week 1 of
   `value` (the Monday beginning that ISO year), matching
   `datetime.date.fromisocalendar(value, 1, 1)`.
2. WHEN the range bounds for a date column are requested for ISO-year mode with
   an integer year `value`, THEN the upper bound SHALL be the last day of the
   ISO year `value` — i.e. one day before the first day of ISO week 1 of
   `value + 1` (`datetime.date.fromisocalendar(value + 1, 1, 1)` minus one day).
3. WHEN date-column bounds are produced in ISO-year mode, THEN each returned
   bound SHALL be passed through the same date-value adaptation applied to
   calendar-year bounds, so the returned values have the same representation as
   before.

## Requirement 2: ISO-year bounds for datetime columns

**User story:** As a developer filtering a `DateTimeField` by ISO
week-numbering year, I want the range optimization to use ISO-year boundaries
with full sub-second and timezone precision, so that the filter returns exactly
the rows whose ISO year equals the queried value.

**Acceptance criteria**

1. WHEN the range bounds for a datetime column are requested for ISO-year mode
   with an integer year `value`, THEN the operations object SHALL return a
   two-element `[lower, upper]` list whose lower bound is midnight at the start
   of the first day of ISO week 1 of `value`, matching
   `datetime.datetime.fromisocalendar(value, 1, 1)`.
2. WHEN the range bounds for a datetime column are requested for ISO-year mode
   with an integer year `value`, THEN the upper bound SHALL be the last
   representable microsecond of the ISO year `value` — i.e. one microsecond
   before midnight at the start of the first day of ISO week 1 of `value + 1`
   (`datetime.datetime.fromisocalendar(value + 1, 1, 1)` minus one microsecond).
3. WHILE timezone support is active, the ISO-year datetime bounds SHALL be made
   timezone-aware in the current timezone before adaptation, exactly as the
   calendar-year datetime bounds are.
4. WHEN datetime-column bounds are produced in ISO-year mode, THEN each returned
   bound SHALL be passed through the same datetime-value adaptation applied to
   calendar-year bounds.

## Requirement 3: Select ISO-year bounds only for ISO-year lookups

**User story:** As a developer, I want the range optimization to switch to
ISO-year bounds precisely when the lookup targets the ISO week-numbering year,
so that `__iso_year` filters are correct without changing any other lookup.

**Acceptance criteria**

1. WHEN a year-based lookup computes its BETWEEN range and the extraction it
   wraps is an ISO-year extraction (`ExtractIsoYear`), THEN it SHALL request
   ISO-year bounds from the operations object.
2. IF the extraction the lookup wraps is not an ISO-year extraction (e.g. an
   ordinary `ExtractYear`), THEN the lookup SHALL request calendar-year bounds,
   preserving the previous behavior.
3. WHEN a year-based lookup computes its BETWEEN range, THEN whether the
   underlying column is a `DateTimeField` (datetime bounds) or otherwise (date
   bounds) SHALL continue to determine which bounds routine is used, and this
   dispatch SHALL be independent of the calendar-vs-ISO year choice.
4. WHEN an `__iso_year` filter compares against a direct integer value, THEN the
   resulting query SHALL select exactly the rows whose date/datetime column
   falls within the ISO-year range for that value, including rows dated in late
   December of the previous calendar year or early January that belong to the
   queried ISO year, and excluding rows that belong to an adjacent ISO year.
5. WHEN an ISO-year extraction is applied as an explicit annotation and that
   annotation is then used in a filter against a direct integer value, THEN the
   filter SHALL yield the same ISO-year range semantics as the implicit
   `__iso_year` lookup.

## Requirement 4: Preserve calendar-year and non-year behavior (regression)

**User story:** As a maintainer, I want all existing calendar-year lookups and
unrelated date-function behavior to remain exactly as before, so that adding
ISO-year support introduces no regressions.

**Acceptance criteria**

1. WHEN calendar-year bounds are requested for a date column with year `value`,
   THEN the lower and upper bounds SHALL remain January 1st and December 31st of
   `value` respectively.
2. WHEN calendar-year bounds are requested for a datetime column with year
   `value`, THEN the lower bound SHALL remain midnight of January 1st of `value`
   and the upper bound SHALL remain the last microsecond of December 31st of
   `value` (`23:59:59.999999`), with timezone-awareness applied when timezone
   support is active.
3. The system SHALL keep the existing calendar-year default: a bounds request
   made without asking for ISO-year mode SHALL behave identically to the prior
   implementation.
4. WHEN a `__year` lookup (or a filter over an `ExtractYear` annotation)
   compares against a direct integer value, THEN it SHALL continue to produce a
   calendar-year `BETWEEN` range and select rows by calendar year.
5. The system SHALL continue to support the full range of year comparison
   lookups (exact, greater-than, greater-than-or-equal, less-than,
   less-than-or-equal) for both calendar-year and ISO-year extractions, each
   using the appropriate bound(s) of the computed range.
6. WHEN an ISO-year extraction is used directly in an annotation (not as a range
   filter), THEN it SHALL continue to compute the ISO week-numbering year via
   the extraction operation, unchanged by this fix.
