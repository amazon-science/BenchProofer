# Requirements: `floatformat` must not crash when rendering a whole value at zero decimal places

## Introduction

The `floatformat` template filter in `django/template/defaultfilters.py` formats a
numeric value (given as a number, a `Decimal`, or a string) to a requested number
of decimal places `arg`. When the value is a whole number and the caller asks for a
*non-positive* number of places, the filter is meant to short-circuit and emit just
the integer part, formatted through the shared locale/grouping step.

Today that short-circuit only triggers for a strictly negative place count. When the
requested place count is exactly `0` and the value is whole (for example `"0.00"` or
`Decimal("0.00")` with `arg` of `0`), the filter instead falls through to the general
rounding path, where it builds a `decimal.Context` whose precision can be `0`. That
raises `ValueError: valid range for prec is [1, MAX_PREC]`, crashing the filter.

The goal is to make the whole-number short-circuit apply whenever the requested place
count is zero *or* negative, so a whole value at zero places renders as a plain
integer, while preserving every other documented formatting behavior of the filter.
The affected code is the `floatformat(text, arg=-1)` function in
`django/template/defaultfilters.py`.

## Requirement 1: Whole values with a non-positive place count render as a plain integer

**User story:** As a template author, I want `floatformat` to format a whole numeric
value with zero requested decimal places as a bare integer, so that a value like
`"0.00"` renders without crashing.

**Acceptance criteria**

1. WHEN `floatformat` is called with a value whose fractional part is zero and a
   requested place count of `0`, THEN the filter SHALL return the integer part of the
   value formatted with zero fractional digits (via the shared locale/grouping number
   formatting step), and SHALL NOT raise an exception.
2. WHEN `floatformat` is called with the string `"0.00"` and a place count of `0`,
   THEN the filter SHALL return `"0"`.
3. WHEN `floatformat` is called with `Decimal("0.00")` and a place count of `0`, THEN
   the filter SHALL return `"0"`.
4. WHEN `floatformat` is called with a whole value and a place count of `0`, THEN the
   filter SHALL NOT construct a rounding precision of `0` and SHALL NOT raise
   `ValueError` for an out-of-range precision.
5. The system SHALL treat a requested place count as non-positive when it is either
   zero or negative for the purpose of selecting the plain-integer rendering of a
   whole value.

## Requirement 2: Existing whole-value and general rounding behavior is preserved

**User story:** As a maintainer, I want the fix to leave all previously supported
`floatformat` outputs unchanged, so that no formatting regressions are introduced.

**Acceptance criteria**

1. WHEN `floatformat` is called with a whole value and a strictly negative place
   count, THEN the filter SHALL continue to return the integer part formatted with no
   fractional digits.
2. WHEN `floatformat` is called with a value that has a non-zero fractional part,
   THEN the filter SHALL render the value rounded/padded to the absolute value of the
   requested place count, regardless of the sign of that count.
3. WHEN `floatformat` is called with a whole value and a strictly positive place
   count, THEN the filter SHALL render exactly that many trailing fractional zeros.
4. WHEN `floatformat` is called with a value and a positive place count that requires
   rounding, THEN the filter SHALL round half-up (round half away from zero) to the
   requested number of places.
5. WHEN `floatformat` is called with only a value and no explicit place count, THEN
   the filter SHALL use a default place count of `-1`, rendering up to one fractional
   digit and dropping the fractional part entirely when the value is whole.
6. WHEN `floatformat` renders a value, THEN the resulting digit text SHALL pass
   through the shared locale/grouping number-formatting step so that localization,
   unlocalization, and thousand-grouping options continue to apply.

## Requirement 3: Argument suffixes and non-numeric inputs behave as before

**User story:** As a template author, I want the grouping/unlocalize suffixes and
error handling to keep working, so that the fix is limited to the whole-value
short-circuit.

**Acceptance criteria**

1. WHEN the place-count argument is a string ending in `g`, THEN the filter SHALL
   force thousand-grouping using the active locale separator and SHALL interpret the
   remaining characters (or `-1` when none remain) as the numeric place count.
2. WHEN the place-count argument is a string ending in `u`, THEN the filter SHALL
   render the result unlocalized and SHALL interpret the remaining characters (or
   `-1` when none remain) as the numeric place count.
3. WHEN the place-count argument is a string ending in `gu` or `ug`, THEN the filter
   SHALL both force grouping and render unlocalized, using the remaining characters
   (or `-1` when none remain) as the numeric place count.
4. IF the place-count argument cannot be interpreted as an integer, THEN the filter
   SHALL return the original input value unchanged.
5. IF the value cannot be interpreted as a number (including `None` and non-numeric
   strings), THEN the filter SHALL return an empty string.
6. WHEN the value is infinity or NaN, THEN the filter SHALL return the string
   representation of that value rather than attempting numeric rounding.
7. WHEN the value is a negative zero or rounds to zero, THEN the filter SHALL render
   it without a spurious negative sign, consistent with prior behavior.
