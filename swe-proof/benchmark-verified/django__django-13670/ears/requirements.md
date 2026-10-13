# Requirements: Two-digit year formatting in `django.utils.dateformat`

## Introduction

Django's template/date formatting utilities live in `django/utils/dateformat.py`.
The `DateFormat` class implements one method per PHP-style format character; the
`y` method is responsible for the "two-digit year" specifier and is reached
through the module-level `dateformat.format(value, format_string)` convenience
function (and `DateFormat.format`).

The current `y` implementation derives the two-digit year by string-slicing the
decimal representation of the year (dropping the first two characters). This is
correct only for four-digit years: for years below 1000 it drops meaningful
digits and never pads, so `y` produces one digit (or an empty string) instead of
a zero-padded two-digit value. This diverges from Python's `datetime.strftime('%y')`
and PHP's `date('y')`, both of which always emit exactly two digits with a
leading zero when needed.

The goal is to make the `y` specifier always yield the last two digits of the
year, zero-padded to a width of two, for every year — including years less than
1000 — while leaving all other format specifiers unchanged.

## Requirement 1: `y` specifier yields the zero-padded two-digit year

**User story:** As a developer formatting dates with the `y` character, I want
the two-digit year to always be exactly two digits with a leading zero when
needed, so that output matches Python's `strftime('%y')` and PHP's `date('y')`
for any year.

**Acceptance criteria**

1. WHEN a date/datetime is formatted with a format string containing the `y`
   character, THEN `django.utils.dateformat.format` SHALL emit for that
   character exactly two characters representing the year taken modulo 100
   (the last two decimal digits of the year).
2. IF the year modulo 100 is less than 10, THEN the `y` output SHALL be
   left-padded with a single `0` so the result is exactly two characters
   (e.g. the year 9 produces `09`).
3. WHEN the year is less than 1000 (a three-digit year such as the 123 shown in
   the issue), THEN the `y` output SHALL be the last two digits of that year
   (`23`), not a truncation of its full string representation (which previously
   yielded a single digit).
4. WHEN the year is less than 100, THEN the `y` output SHALL be the last two
   digits of that year rendered as two characters, and WHEN the year is less
   than 10 (as with the single-digit case noted in the issue), THEN the `y`
   output SHALL be that year zero-padded to two digits.
5. The `y` output SHALL always be a string of length two for every valid year.

## Requirement 2: Preserve existing two-digit-year and other-specifier behavior

**User story:** As a maintainer, I want the fix to change only the sub-1000-year
behavior of `y`, so that all previously correct formatting continues to work.

**Acceptance criteria**

1. WHEN the year is 1000 or greater, THEN the `y` output SHALL remain the last
   two digits of the year (e.g. 1979 produces `79`), matching prior behavior.
2. The system SHALL keep the four-digit year specifier `Y` returning the full
   year, unaffected by this change.
3. The system SHALL keep every other date and time format specifier producing
   the same output as before (day, month, weekday, hour, minute, second,
   microsecond, am/pm, timezone, epoch, day-of-year, and related specifiers),
   so that existing date, time, and datetime formatting is unchanged.
4. WHEN a format string mixes the `y` character with other specifiers and
   literal characters, THEN `dateformat.format` SHALL substitute each specifier
   independently and preserve literal text, with only the `y` substitution
   reflecting the corrected two-digit behavior.
