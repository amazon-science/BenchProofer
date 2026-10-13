# Requirements — `timesince()` timezone-aware long intervals

## Introduction

`django.utils.timesince.timesince()` (and its wrapper `timeuntil()`) formats the
elapsed interval between two datetime values as a human-readable string such as
`"1 month"` or `"2 weeks, 3 days"`. To account for the varying length of years
and months, the function computes a whole number of years and months and then
builds an intermediate reference datetime — a "pivot" — shifted from the start
value `d` by that many years and months. It measures the sub-month remainder by
subtracting that pivot from the later value.

When the interval spans at least one month (so years or months are non-zero) the
pivot is constructed with `datetime.datetime(...)` from the year, month, day,
hour, minute, and second derived from `d`. At the affected base revision this
construction omits the timezone designation, so the pivot is always
timezone-naive. When `d` is timezone-aware (as it is when the project configures
timezone support and passes aware datetimes), the later subtraction mixes an
aware value with a naive pivot and raises
`TypeError: can't subtract offset-naive and offset-aware datetimes`.

The goal is that `timesince()`/`timeuntil()` produce correct results for
timezone-aware inputs across the full range of intervals — including intervals
of a month or more — without raising, while every existing behavior for naive
inputs, short intervals, depth control, and edge cases is preserved. The change
is localized to the pivot construction inside `timesince()` in
`django/utils/timesince.py`; `MONTHS_DAYS` and the surrounding arithmetic are
unchanged.

## Requirement 1: Timezone-aware long intervals must not raise

**User story:** As a developer using timezone-aware datetimes, I want
`timesince()` to work for intervals of a month or more, so that displaying "time
since" values does not crash when timezone support is enabled.

**Acceptance criteria**
1. WHEN `timesince(d)` (or `timesince(d, now)`) is called with `d` timezone-aware
   and the interval between `d` and the comparison value is one month or longer,
   THEN `timesince` SHALL return the formatted interval string and SHALL NOT
   raise a `TypeError`.
2. WHEN the pivot reference datetime is constructed for an interval that includes
   whole years and/or months, THEN the constructed pivot SHALL carry the same
   timezone designation as `d` (aware with `d`'s UTC offset when `d` is aware;
   naive when `d` is naive), so that it is directly comparable with the other
   datetime it is subtracted from.
3. WHEN `d` is timezone-aware and one month or more in the past, THEN
   `timesince(d)` SHALL report the correct number of elapsed months (e.g. an
   interval of about 31 days SHALL be reported as `"1 month"`).
4. The system SHALL apply the same timezone-aware handling to `timeuntil()`,
   which measures the interval in the opposite direction using the same
   computation.

## Requirement 2: Correct multi-unit and depth-limited output for aware inputs

**User story:** As a developer, I want the years/months/weeks/days/hours/minutes
breakdown and the `depth` limit to behave identically for aware and naive
inputs, so that timezone support does not change formatting.

**Acceptance criteria**
1. WHEN the interval spans multiple adjacent units, THEN `timesince` SHALL return
   up to `depth` adjacent non-zero units, largest first, joined by `", "` (for
   example an interval of a year plus a month plus a week plus a day plus an hour
   yields `"1 year"` at depth 1, `"1 year, 1 month"` at depth 2, and so on).
2. WHEN two non-zero units are not adjacent, THEN `timesince` SHALL return only
   the first (largest) unit.
3. The system SHALL produce these breakdown and depth behaviors identically
   whether the inputs are timezone-aware or timezone-naive.
4. IF `depth` is less than or equal to 0, THEN `timesince` SHALL raise a
   `ValueError` whose message states that depth must be greater than 0, for both
   aware and naive inputs.

## Requirement 3: Month and year boundary correctness

**User story:** As a developer, I want month and year counts to respect the real
lengths of calendar months and years, so that boundary dates are reported
accurately regardless of timezone awareness.

**Acceptance criteria**
1. WHEN computing the pivot's day-of-month, THEN the system SHALL clamp `d`'s day
   to the last valid day of the pivot's month, so that a start day that does not
   exist in the target month does not overflow into the following month.
2. WHEN the interval crosses month boundaries of differing lengths, THEN
   `timesince` SHALL report the month count and the sub-month remainder consistent
   with actual calendar month lengths (the same results across a full sweep of
   end-of-month and start-of-month dates).
3. WHEN the interval spans a very long period (e.g. on the order of a thousand
   years), THEN `timesince` SHALL report the correct number of years for both
   aware and naive inputs.
4. The system SHALL produce correct results across leap-year boundaries,
   including intervals that begin near the end of a leap year.

## Requirement 4: Preserve existing behavior for short intervals, future values, and naive inputs

**User story:** As a maintainer, I want all previously working behaviors to keep
working, so that adding timezone-aware support introduces no regressions.

**Acceptance criteria**
1. WHEN the comparison value is equal to or earlier than `d` (the target is in
   the past relative to `d`), THEN `timesince` SHALL return the zero-minutes
   string (`"0 minutes"` in the default locale).
2. WHEN the interval is smaller than one minute (only seconds or microseconds),
   THEN `timesince` SHALL ignore those sub-minute components and return the
   zero-minutes string.
3. WHEN either argument is a `datetime.date` rather than a `datetime.datetime`,
   THEN `timesince`/`timeuntil` SHALL still compute and format the interval
   correctly.
4. WHEN called with timezone-naive datetimes, THEN `timesince` SHALL continue to
   behave exactly as before (no exception, unchanged results).
5. WHEN the comparison uses two datetimes in different timezones, THEN
   `timesince`/`timeuntil` SHALL compute the interval based on the actual instant
   each represents.
6. IF a datetime carries timezone information that reports no defined UTC offset,
   THEN `timesince`/`timeuntil` SHALL treat that value as timezone-naive and
   return a correct result without raising.
7. WHEN a custom `time_strings` mapping is supplied, THEN `timesince` SHALL use
   those strings in place of the defaults when formatting the result.
