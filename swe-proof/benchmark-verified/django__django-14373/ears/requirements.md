# Requirements: Zero-padded four-digit year in date formatting

## Introduction

Django's date-formatting utility (`django.utils.dateformat`) renders a date/time
value into a string according to a format string. Each format character is
handled by a method on the `DateFormat` / `TimeFormat` formatter classes, and the
`Formatter.format` driver joins the pieces after coercing each handler's return
value with `str()`.

The `Y` format specifier is documented to produce the year as four digits (for
example `'1999'`). For years before the year 1000 this contract was broken: the
handler returned the year as a bare integer, so after string coercion a year such
as `1` rendered as `'1'` and `999` rendered as `'999'` rather than as four-digit,
zero-left-padded text. The goal is to make the `Y` specifier always yield a
four-digit, zero-padded representation of the year, while leaving every other
format specifier's behavior unchanged.

## Requirement 1: `Y` specifier always renders a zero-padded four-digit year

**User story:** As a developer formatting dates, I want the `Y` specifier to
always produce a four-digit year, so that years before 1000 line up with the
documented four-digit format and sort/display consistently.

**Acceptance criteria**
1. WHEN a date or datetime value is formatted with a format string containing the
   `Y` specifier and the value's year is less than 1000, THEN the formatting
   utility SHALL render the year as a string that is left-padded with the `'0'`
   character to a minimum width of four characters.
2. WHEN the `Y` specifier is applied to a value whose year is `1`, THEN the
   rendered text for that specifier SHALL be `0001`.
3. WHEN the `Y` specifier is applied to a value whose year is `999`, THEN the
   rendered text for that specifier SHALL be `0999`.
4. IF the year's ordinary base-ten representation already has four or more
   digits, THEN the `Y` specifier SHALL render the year in full with no
   truncation and no additional leading zeros (for example a year of `1999`
   renders as `1999`).
5. The `Y` specifier SHALL render only the decimal digits of the year with the
   leading-zero padding described above, introducing no sign, separator, or other
   extra characters.
6. WHEN the `Y` specifier's rendered value is joined into the surrounding
   formatted output, THEN the leading zeros SHALL be preserved in the final
   string (the padded four-digit form SHALL survive the utility's string
   coercion and joining step).

## Requirement 2: Preserve existing behavior of the two-digit `y` specifier

**User story:** As a developer relying on the existing two-digit year specifier,
I want its behavior to remain unchanged, so that existing formatted output does
not regress.

**Acceptance criteria**
1. WHEN a value is formatted with the `y` specifier, THEN the formatting utility
   SHALL render exactly the last two decimal digits of the year (the year taken
   modulo one hundred), left-padded with `'0'` to a minimum width of two
   characters and never wider than two characters.
2. IF the year's final two digits form a value less than ten, THEN the `y`
   specifier SHALL emit a single leading `'0'` so that the rendered text is
   exactly two characters wide.
3. IF the year is greater than or equal to one hundred, THEN the `y` specifier
   SHALL render only those final two digits, discarding every higher-order
   digit, and SHALL leave this two-digit behavior unchanged by the four-digit
   `Y` fix.

## Requirement 3: Preserve all other date/time formatting behavior

**User story:** As a maintainer, I want every format specifier other than `Y` to
keep its current behavior, so that the change is limited to fixing the four-digit
year padding.

**Acceptance criteria**
1. The formatting utility SHALL continue to render all format specifiers other
   than `Y` exactly as before this change, including day, month, weekday, time,
   time-zone, microsecond, day-of-year, week-number, and epoch-second
   specifiers.
2. The formatting utility SHALL continue to treat backslash-escaped characters in
   the format string as literal text, emitting the escaped character without
   interpreting it as a specifier.
3. IF a time-related specifier is used against a plain date value, THEN the
   formatting utility SHALL continue to raise the same error it raised before this
   change.
4. WHEN an empty format string is supplied, THEN the formatting utility SHALL
   continue to return an empty string.
