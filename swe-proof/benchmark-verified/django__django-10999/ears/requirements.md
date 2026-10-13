# Requirements: Correct parsing of negative durations in `parse_duration()`

## Introduction

`django.utils.dateparse.parse_duration(value)` converts a duration string into a
`datetime.timedelta`, supporting Django's preferred `'%d %H:%M:%S.%f'` layout,
ISO 8601 durations, and PostgreSQL day-time intervals. The standard day-time
layout is recognized by a regular expression in `django/utils/dateparse.py`.

For the standard day-time layout, a leading minus sign is meant to negate the
whole time-of-day portion (hours, minutes, seconds and fractional seconds
together). The current recognizer mishandles this: when a negative value carries
an hours component it fails to recognize the string, and when it does recognize
a negative value it applies the sign to only part of the components, producing
the wrong `timedelta`. The goal is to make the standard layout accept negative
day-time durations and negate every time component consistently, while leaving
all other accepted inputs, and the ISO 8601 and PostgreSQL layouts, unchanged.

This document specifies the observable behavior of `parse_duration()` for the
affected module `django/utils/dateparse.py`. Numeric strings mentioned below are
illustrative of a behavior rule, not an enumeration of required cases.

## Requirement 1: A leading sign negates the entire time-of-day portion

**User story:** As a developer parsing duration strings, I want a leading minus
sign on a standard day-time duration to negate the entire time-of-day, so that
the resulting `timedelta` matches the intuitive negative value.

**Acceptance criteria**

1. WHEN `parse_duration()` receives a standard day-time string whose time
   portion is prefixed by a single leading minus sign, THEN `parse_duration()`
   SHALL return a `timedelta` in which the hours, minutes, seconds and
   fractional-seconds contributions are all treated as negative — the sign
   applies to the whole time-of-day together, never to only some of the
   components.
2. WHEN the signed time-of-day is written in the hours:minutes:seconds form,
   THEN `parse_duration()` SHALL recognize and parse it (rather than failing to
   match), negating all three components; it SHALL NOT leave the hours positive
   or fall back to a mostly-positive value with only one component negated.
3. WHEN the signed time-of-day is written in the minutes:seconds form, THEN
   `parse_duration()` SHALL return a value in which both the minutes and the
   seconds are negative.
4. WHEN the signed time-of-day's seconds component carries a fractional part,
   THEN `parse_duration()` SHALL return a value in which both the whole-seconds
   contribution and its sub-second (microsecond) portion are negative; the
   leading sign SHALL extend to the fractional part rather than stopping at the
   whole seconds.

## Requirement 2: A sign is accepted only once, ahead of the time components

**User story:** As a developer, I want the standard layout to accept a single
sign for the time-of-day and to reject strings that place a sign in front of an
interior component, so that only well-formed negative durations parse.

**Acceptance criteria**

1. WHEN `parse_duration()` receives a standard day-time string in which a minus
   sign appears immediately before an interior time component (that is, a sign
   in front of a minutes or seconds field that follows a colon), THEN
   `parse_duration()` SHALL treat the string as not well formed and return
   `None`; it SHALL NOT interpret such a string as a valid duration value.
2. The system SHALL accept at most one sign for the time-of-day portion of a
   standard day-time duration, positioned immediately before the leading time
   component.

## Requirement 3: The days component keeps its own independent sign

**User story:** As a developer, I want the leading day count to carry its own
sign independent of the time-of-day sign, so that mixed-sign day durations keep
their existing meaning.

**Acceptance criteria**

1. WHEN `parse_duration()` receives a standard duration with a signed day count
   followed by an unsigned time portion, THEN `parse_duration()` SHALL apply the
   sign only to the days and leave the time components positive; the day sign and
   the time-of-day sign SHALL be independent of each other.
2. WHEN `parse_duration()` receives a bare signed integer with no colon (a signed
   seconds count), THEN `parse_duration()` SHALL return a `timedelta` equal to
   that many negative seconds (which may normalize into whole negative days).

## Requirement 4: Preserve positive standard-format parsing

**User story:** As a developer, I want all previously accepted positive standard
durations to parse exactly as before, so that this change introduces no
regression.

**Acceptance criteria**

1. WHEN `parse_duration()` receives a positive hours:minutes:seconds string
   (for example `'10:15:30'`), THEN `parse_duration()` SHALL return the
   corresponding positive `timedelta` (here `timedelta(hours=10, minutes=15,
   seconds=30)`), including for hour/minute/second fields larger than the usual
   clock ranges.
2. WHEN `parse_duration()` receives a positive minutes:seconds string (for
   example `'15:30'`), THEN `parse_duration()` SHALL return the corresponding
   positive `timedelta` (`timedelta(minutes=15, seconds=30)`).
3. WHEN `parse_duration()` receives a positive bare seconds string (for example
   `'30'`), THEN `parse_duration()` SHALL return `timedelta(seconds=30)`.
4. WHEN `parse_duration()` receives a positive day duration (for example
   `'4 15:30'` or `'4 10:15:30'`), THEN `parse_duration()` SHALL return the
   corresponding `timedelta` with positive days and time components.
5. WHEN `parse_duration()` receives a positive standard duration with a
   fractional-seconds part (for example `'15:30.1'`), THEN `parse_duration()`
   SHALL return a value whose sub-second portion reflects the given fraction
   padded to microseconds.
6. WHEN `parse_duration()` receives the string produced by formatting a
   `timedelta` with `str()` (Django's preferred `'%d %H:%M:%S.%f'` output),
   THEN `parse_duration()` SHALL return a `timedelta` equal to the original,
   including for values whose day count is negative while the time-of-day is
   written unsigned.

## Requirement 5: Preserve ISO 8601 and PostgreSQL interval parsing

**User story:** As a developer, I want ISO 8601 durations and PostgreSQL
day-time intervals to keep parsing exactly as before, so that the standard-layout
change does not disturb the other supported formats.

**Acceptance criteria**

1. WHEN `parse_duration()` receives an ISO 8601 duration, THEN
   `parse_duration()` SHALL return the same result as before this change, and
   inputs that were not accepted as ISO 8601 durations before SHALL continue to
   return `None`.
2. WHEN `parse_duration()` receives a PostgreSQL day-time interval, THEN
   `parse_duration()` SHALL return the same result as before this change,
   including the case where a signed day count combines with a separately signed
   time-of-day; the standard-layout change SHALL NOT alter how these intervals,
   or the independent day/time signs within them, are interpreted.
3. IF an input string is not well formed under any of the supported layouts,
   THEN `parse_duration()` SHALL return `None`.
