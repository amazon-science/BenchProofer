# Requirements: Correct two-digit year interpretation in HTTP date parsing

## Introduction

`django.utils.http.parse_http_date` parses the three date formats permitted by
HTTP (RFC 7231 §7.1.1.1): RFC 1123, RFC 850, and asctime. The RFC 850 format
carries a **two-digit year**, which the parser must expand into a full
four-digit year.

The existing implementation expands two-digit years with a hard-coded rule:
values `0`–`69` map to `2000`–`2069` and values `70`–`99` map to `1970`–`1999`.
RFC 7231 instead requires that the expansion be made **relative to the current
year**: a timestamp whose two-digit year appears to be more than 50 years in
the future must be interpreted as the most recent past year that has the same
last two digits.

The goal is to make `parse_http_date` (in `django/utils/http.py`) expand
two-digit years according to this sliding, current-year-relative rule, while
preserving all other parsing behavior (RFC 1123, asctime, four-digit years,
error handling, and the `parse_http_date_safe` wrapper).

## Requirement 1: Interpret two-digit years relative to the current year

**User story:** As a developer relying on Django's HTTP date parsing, I want
two-digit years in RFC 850 dates to be interpreted relative to the current
year, so that dates conform to RFC 7231 and remain correct as time passes.

**Acceptance criteria**

1. WHEN `parse_http_date` parses a date whose year field has fewer than three
   digits (a two-digit year in the range `0`–`99`), THEN `parse_http_date`
   SHALL expand it to a full four-digit year whose last two digits equal the
   original two-digit value.
2. The system SHALL treat the year of the current UTC date as the reference
   point for this expansion.
3. IF placing the two-digit year in the current century would produce a year
   more than 50 years after the current year, THEN `parse_http_date` SHALL
   instead interpret it as the most recent earlier year having those same last
   two digits (i.e. the same last two digits, one century earlier).
4. IF placing the two-digit year in the current century would produce a year
   no more than 50 years after the current year, THEN `parse_http_date` SHALL
   interpret it as that year in the current century.
5. The system SHALL ensure the expanded four-digit year is never more than 50
   years later than the current year.
6. WHEN a two-digit year is parsed, THEN `parse_http_date` SHALL place it in
   the current century if and only if that two-digit value minus the last two
   digits of the current year is no greater than 50; otherwise it SHALL place
   it one century earlier. (The century boundary therefore depends on the
   current year, not on a fixed threshold such as 70.)

## Requirement 2: Preserve existing parsing of the other date behaviors

**User story:** As a maintainer, I want the fix to change only two-digit year
handling, so that all other date-parsing behavior continues to work unchanged.

**Acceptance criteria**

1. WHEN `parse_http_date` receives a date whose year field already has four
   digits (a full year), THEN `parse_http_date` SHALL use that year verbatim
   without any century adjustment.
2. WHEN `parse_http_date` receives a valid RFC 1123 date, THEN it SHALL return
   the number of seconds since the Unix epoch (UTC) corresponding to that date
   and time.
3. WHEN `parse_http_date` receives a valid asctime-format date, THEN it SHALL
   return the number of seconds since the Unix epoch (UTC) corresponding to
   that date and time.
4. WHEN `parse_http_date` receives a valid RFC 850 date, THEN it SHALL return
   the number of seconds since the Unix epoch (UTC) corresponding to that date
   and time, with its two-digit year expanded per Requirement 1.
5. IF the input does not match any of the three accepted date formats, THEN
   `parse_http_date` SHALL raise `ValueError`.
6. IF the input matches a format but denotes an impossible calendar date or
   time, THEN `parse_http_date` SHALL raise `ValueError`.
7. WHEN `parse_http_date_safe` receives an input that would cause
   `parse_http_date` to raise, THEN `parse_http_date_safe` SHALL return
   `None` rather than raising.
