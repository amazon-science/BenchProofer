# Requirements: Honor an explicit `tzinfo` in `TruncDate` and `TruncTime`

## Introduction

The database functions `TruncDate` and `TruncTime`
(`django.db.models.functions.datetime`) cast a stored datetime expression to a
date or a time inside the database. Both classes derive from `TruncBase`, which
mixes in `TimezoneMixin` and therefore accepts an optional `tzinfo` argument
alongside the ambient project timezone.

Timezone conversion must be applied to the input datetime *before* the value is
reduced to a date or a time, because the calendar date (and wall-clock time) of a
single instant differs between timezones. The shared helper
`TimezoneMixin.get_tzname()` already encodes the correct zone-selection policy
used by the sibling functions (`Extract`, `TruncBase` for datetime output): under
timezone support it prefers an explicitly supplied `tzinfo` over the current
timezone, and yields no zone when timezone support is disabled.

`TruncDate` and `TruncTime` each override `as_sql` and select the conversion zone
independently of that helper: they take the current timezone name whenever
`settings.USE_TZ` is true and discard any `tzinfo` the caller passed. As a
result, aggregating or annotating by date/time in a non-ambient timezone produces
values for the wrong zone. The goal is to make both functions resolve the
conversion zone through the same policy the rest of the family uses, so an
explicit `tzinfo` is respected, while every previously-correct behavior is
preserved.

Affected code: `django/db/models/functions/datetime.py` — the `as_sql` methods of
`TruncDate` and `TruncTime`; the `TimezoneMixin.get_tzname()` helper; the backend
operations `datetime_cast_date_sql` and `datetime_cast_time_sql`.

## Requirement 1: `TruncDate` honors an explicit conversion timezone

**User story:** As a developer annotating or aggregating datetimes by calendar
date, I want to pass a specific timezone into `TruncDate` so that the resulting
dates reflect that timezone rather than only the project's ambient timezone.

**Acceptance criteria**

1. WHEN a `TruncDate` expression is compiled to SQL while timezone support is
   enabled and an explicit `tzinfo` was supplied, THEN `TruncDate` SHALL resolve
   the conversion zone from that supplied `tzinfo` (its zone name) and SHALL pass
   that zone name to the database date-cast operation
   (`datetime_cast_date_sql`).
2. WHEN the stored instant is converted using the supplied timezone, THEN the
   date produced by `TruncDate` SHALL equal the calendar date of that instant as
   observed in the supplied timezone (i.e. the date of the input datetime after
   conversion to that zone), not the date observed in the ambient timezone.
3. IF two `TruncDate` expressions over the same stored instant are given two
   different timezones whose local calendar dates differ, THEN the two results
   SHALL be different dates, each matching its own timezone.
4. WHEN timezone support is enabled and NO explicit `tzinfo` was supplied, THEN
   `TruncDate` SHALL resolve the conversion zone from the current (ambient)
   timezone name, preserving its prior default behavior.
5. IF timezone support is disabled, THEN `TruncDate` SHALL pass no timezone
   (a null zone) to the date-cast operation, regardless of any `tzinfo`.
6. The system SHALL leave the compilation of the inner datetime expression and
   the resulting query parameters unchanged; only the conversion zone name passed
   to the date cast is affected.

## Requirement 2: `TruncTime` honors an explicit conversion timezone

**User story:** As a developer extracting the wall-clock time from stored
datetimes, I want to pass a specific timezone into `TruncTime` so that the
resulting times reflect that timezone rather than only the project's ambient
timezone.

**Acceptance criteria**

1. WHEN a `TruncTime` expression is compiled to SQL while timezone support is
   enabled and an explicit `tzinfo` was supplied, THEN `TruncTime` SHALL resolve
   the conversion zone from that supplied `tzinfo` (its zone name) and SHALL pass
   that zone name to the database time-cast operation
   (`datetime_cast_time_sql`).
2. WHEN the stored instant is converted using the supplied timezone, THEN the
   time produced by `TruncTime` SHALL equal the wall-clock time of that instant as
   observed in the supplied timezone, not the time observed in the ambient
   timezone.
3. IF two `TruncTime` expressions over the same stored instant are given two
   different timezones whose local wall-clock times differ, THEN the two results
   SHALL be different times, each matching its own timezone.
4. WHEN timezone support is enabled and NO explicit `tzinfo` was supplied, THEN
   `TruncTime` SHALL resolve the conversion zone from the current (ambient)
   timezone name, preserving its prior default behavior.
5. IF timezone support is disabled, THEN `TruncTime` SHALL pass no timezone
   (a null zone) to the time-cast operation, regardless of any `tzinfo`.
6. The system SHALL leave the compilation of the inner datetime expression and
   the resulting query parameters unchanged; only the conversion zone name passed
   to the time cast is affected.

## Requirement 3: Consistent zone-selection policy across the Trunc/Extract family

**User story:** As a maintainer, I want `TruncDate` and `TruncTime` to follow the
same timezone-resolution rule as the rest of the date/time database functions, so
that the `tzinfo` parameter behaves consistently everywhere it is accepted.

**Acceptance criteria**

1. The system SHALL resolve the conversion zone for `TruncDate` and `TruncTime`
   using the shared `TimezoneMixin.get_tzname()` policy: under timezone support,
   an explicitly supplied `tzinfo` takes precedence over the current timezone;
   with no `tzinfo`, the current timezone is used; with timezone support disabled,
   no zone is used.
2. WHEN an explicit `tzinfo` is supplied to a datetime-output truncation
   (e.g. `TruncYear`) and to `TruncDate`/`TruncTime` over the same stored instant,
   THEN all of them SHALL apply the same supplied timezone when determining the
   result.
3. The system SHALL keep the existing `tzinfo`-honoring behavior of `Extract`
   and of `TruncBase` for datetime output fields unchanged.

## Requirement 4: Preserve existing truncation and extraction behavior

**User story:** As an existing user, I want all previously-working truncation and
extraction operations to keep behaving exactly as before, so that adding explicit
timezone support introduces no regressions.

**Acceptance criteria**

1. The system SHALL continue to truncate datetimes to year, quarter, month, week,
   day, hour, minute, and second, and to extract year, ISO year, quarter, month,
   week, weekday, ISO weekday, day, hour, minute, and second, producing the same
   results as before.
2. WHEN the truncated or extracted input value is null, THEN the corresponding
   `TruncDate`, `TruncTime`, and other Trunc/Extract expressions SHALL yield a
   null result.
3. The system SHALL preserve the behavior of `TruncDate` and `TruncTime` when no
   explicit timezone is involved (default project timezone with support on, or no
   timezone with support off), matching the results produced before this change.
4. The system SHALL continue to support `TruncDate`/`TruncTime` and other
   Trunc/Extract expressions used inside subqueries with parameters, producing the
   same values as before.
5. IF a stored instant falls on an ambiguous or nonexistent local time in the
   converted timezone (a DST transition), THEN `TruncDate` and `TruncTime` SHALL
   still resolve to a valid date/time consistent with the converted instant, as
   the family already does for other truncations.
6. The system SHALL continue to reject invalid input/output field combinations
   for truncation and extraction with the same validation errors as before
   (e.g. truncating a date field to a time component, or extracting a time
   component from a date field).
```
