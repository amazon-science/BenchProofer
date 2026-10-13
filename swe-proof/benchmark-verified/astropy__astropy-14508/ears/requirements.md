# Requirements: minimal-length string rendering of float values in FITS cards

## Introduction

`astropy.io.fits.Card` renders a header card as an 80-character fixed-width
string of the form `KEYWORD = value / comment`. The textual form of a floating
point value is produced by the helper `_format_float(value)` in
`astropy/io/fits/card.py`, and the value field must be kept short (at most 20
characters) so that a value together with its trailing comment can fit on the
card.

The current implementation formats the value with a fixed 16-significant-digit
format (`f"{value:.16G}"`). For many values this produces a textual form that is
longer than necessary — for example the value `0.009125` is expanded to
`0.009124999999999999`. When the value field is longer than needed, the space
left for the comment shrinks and the comment is truncated, so some
keyword/value/comment combinations that are perfectly valid FITS cannot be
constructed through `io.fits.Card`.

The goal is to render each float using its *shortest* round-trippable decimal
form (the form Python's `str(value)` / `repr` produces) so that no value is
needlessly expanded, while preserving the existing FITS-legal formatting
guarantees: presence of a decimal point or exponent, an upper-case exponent
marker, and the 20-character length cap with its truncation rules. This affects
`_format_float`, and therefore `Card.image` / `str(Card)` and the formatting of
complex values (whose real and imaginary parts are formatted with the same
helper).

## Requirement 1: Render floats from their shortest decimal form

**User story:** As a user creating a FITS card from a float value, I want the
value written with the fewest characters that still round-trip to the same
number, so that the value field does not consume space that the comment needs.

**Acceptance criteria**

1. WHEN `_format_float` formats a finite float value, THEN the helper SHALL
   derive the value string from the value's shortest standard decimal
   representation (the string produced by Python's `str`/`repr` of the float),
   not from a fixed 16-significant-digit expansion.
2. WHEN a float value has a shortest decimal representation that is 20
   characters or fewer, THEN `_format_float` SHALL return that representation
   unchanged (apart from the exponent-marker normalization of Requirement 2).
3. WHEN a card is created with a long (`HIERARCH`) keyword, value `0.009125`,
   and a comment, THEN the rendered card string SHALL contain the value field
   exactly as `0.009125` (not an expanded form such as `0.009124999999999999`).
4. WHEN a card is created with a float value whose shortest decimal
   representation has only a few significant digits (whether positive or
   negative), THEN the rendered value field SHALL be exactly that shortest
   representation, with no additional trailing digits appended.
5. IF the shortest representation of a float would otherwise not fit and force
   truncation of an accompanying comment even though a valid shorter-or-equal
   form exists, THEN `_format_float` SHALL prefer the shortest form so that the
   comment is not truncated unnecessarily.

## Requirement 2: Preserve FITS-legal numeric formatting

**User story:** As a consumer of FITS headers, I want float value strings to
remain FITS-legal, so that written cards continue to parse and match the
established formatting.

**Acceptance criteria**

1. The system SHALL ensure every formatted float value string contains either a
   decimal point or an exponent marker, so that it is recognizable as a
   floating point (never an integer-looking) value.
2. WHEN the formatted representation uses scientific notation, THEN
   `_format_float` SHALL write the exponent marker as an upper-case `E` (any
   lower-case `e` produced by the underlying representation SHALL be
   upper-cased).
3. WHEN a float value's shortest representation is a whole number (for example
   `1.0`), THEN the returned string SHALL still include the decimal portion
   rather than dropping it.
4. WHEN a float value requires scientific notation (for example a value on the
   order of `1e+32` or `1e-32`), THEN `_format_float` SHALL return a value
   string whose significand and signed exponent reproduce the value and whose
   marker is upper-case `E`.

## Requirement 3: Enforce the 20-character length cap

**User story:** As a maintainer, I want overly long value strings shortened
deterministically, so that the value always fits within the card's value field.

**Acceptance criteria**

1. WHEN the formatted value string is longer than 20 characters and contains no
   exponent marker, THEN `_format_float` SHALL return only the first 20
   characters of that string.
2. WHEN the formatted value string is longer than 20 characters and contains an
   exponent marker, THEN `_format_float` SHALL keep the exponent suffix (from
   the marker to the end of the string) intact and truncate the leading
   significand so that the returned string is exactly 20 characters long.
3. The system SHALL return a value string of at most 20 characters for every
   finite float input.

## Requirement 4: Keep existing card behaviors intact

**User story:** As an existing user of `io.fits`, I want the change to be
limited to shortening float value strings, so that all other card behaviors
continue to work unchanged.

**Acceptance criteria**

1. The system SHALL continue to render complex values by formatting the real
   and imaginary parts with the same float-formatting rules and combining them
   into the existing parenthesized value form.
2. The system SHALL continue to represent non-finite float values (positive and
   negative infinity, and NaN) using their established textual forms without
   error.
3. WHEN a card's keyword, value, and comment together fit within the card
   width, THEN `str(Card)` SHALL NOT emit a "card is too long / comment will be
   truncated" warning and SHALL NOT truncate the comment.
4. The system SHALL keep the round-trip behavior of reading a card from a header
   and re-creating an equivalent `Card` from its keyword, value, and comment,
   so that a value read as `0.009125` can be re-created and rendered as
   `0.009125`.
5. The system SHALL preserve the existing rendering of ordinary float value
   cards (including negative values and values written in scientific notation)
   so that previously valid card string representations remain unchanged.
