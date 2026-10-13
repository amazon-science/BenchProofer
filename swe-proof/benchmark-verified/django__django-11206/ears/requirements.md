# Requirements: precision-aware rendering of very small decimal values

## Introduction

The number-formatting helper `django.utils.numberformat.format` turns a numeric
value into a display string given a decimal separator, an optional number of
visible decimal places (`decimal_pos`), digit-grouping options, a thousands
separator, grouping toggles, and a localization toggle.

When a caller asks for a fixed number of visible decimal places, a value whose
absolute magnitude is smaller than anything those places can express is
currently shown in exponential notation (for example, a value on the order of
ten-to-the-minus-two-hundred is rendered as `1.00e-200` even though only two
decimal places were requested). Because none of the requested decimal places
can be affected by such a value, the intuitive and correct display is a plain
zero padded to the requested precision (for example `0.00`).

The goal is to make `django.utils.numberformat.format` render any `Decimal`
whose magnitude is too small to influence the requested decimal places exactly
as it would render zero, while leaving every other formatting behavior — large
values, ordinary values, grouping, sign handling, and non-`Decimal` inputs —
unchanged.

## Requirement 1: Treat sub-precision decimals as zero

**User story:** As a developer formatting monetary or measurement values with a
fixed number of decimal places, I want values too small to appear in those
places to be shown as a plain zero, so that displays never surprise me with
exponential notation for negligible magnitudes.

**Acceptance criteria**

1. The system SHALL define, for a requested number of visible decimal places,
   a smallest representable magnitude equal to one unit in the least significant
   requested place — that is, ten raised to the negative of the requested number
   of decimal places (for two requested places this magnitude is `0.01`).
2. WHEN `django.utils.numberformat.format` is called with a `Decimal` value and
   a requested number of decimal places, AND the absolute value of that
   `Decimal` is strictly less than the smallest representable magnitude for that
   number of places, THEN the function SHALL produce exactly the string it would
   produce for a zero value formatted with the same options (an integer part of
   `0` followed, when decimal places are requested, by that many zero digits after
   the decimal separator, e.g. `0.00` for two places).
3. WHEN the requested number of decimal places is zero, THEN the smallest
   representable magnitude SHALL be one tenth (`0.1`), so that a `Decimal` whose
   absolute value is below one tenth SHALL be rendered as `0`.
4. IF the absolute value of the `Decimal` is equal to or greater than the
   smallest representable magnitude for the requested number of places, THEN the
   function SHALL render the value on its own without treating it as zero (for
   example, with two decimal places requested, a value exactly equal to the
   smallest representable magnitude renders its own digits as `0.01`, while any
   value strictly below it renders as `0.00`).
5. WHEN a `Decimal` value is treated as zero under this rule, THEN this
   adjustment SHALL take effect before any decision about using exponential
   notation, so that an extremely small magnitude (for example on the order of
   ten-to-the-minus-two-hundred) requested with a fixed number of decimal places
   SHALL render as a padded zero (such as `0.00` for two places) and SHALL NOT
   render in exponential notation (such as `1.00e-200`).

## Requirement 2: Preserve exponential notation for very large decimals

**User story:** As a developer formatting extremely large decimals, I want them
to keep rendering in compact exponential notation, so that formatting does not
consume excessive memory or change existing output.

**Acceptance criteria**

1. WHEN a `Decimal` value has a magnitude large enough to require more than
   roughly two hundred total digits to write in fixed-point form, THEN
   `django.utils.numberformat.format` SHALL render it in exponential notation,
   formatting the coefficient to the requested number of decimal places when one
   is given, exactly as it did before this change.
2. WHEN no number of decimal places is requested and a `Decimal` has a magnitude
   requiring more than roughly two hundred total digits — whether very large or
   very small — THEN the function SHALL render it in exponential notation on its
   own, unchanged by this fix.
3. The system SHALL keep applying the sub-precision zero adjustment of
   Requirement 1 only to `Decimal` values that request a fixed number of decimal
   places, so that the large-magnitude exponential behavior of this requirement
   is never suppressed by that adjustment.

## Requirement 3: Preserve ordinary decimal formatting

**User story:** As a developer relying on established number formatting, I want
ordinary decimal values, grouping, truncation, padding, and sign handling to be
unchanged, so that existing output is not regressed by the small-value fix.

**Acceptance criteria**

1. WHEN a `Decimal` with a fractional part is formatted with a requested number
   of decimal places, THEN the function SHALL truncate or zero-pad the fractional
   digits to exactly that many places and SHALL preserve a leading minus sign for
   negative values, exactly as before this change.
2. WHEN a `Decimal` with no fractional part is formatted with a requested number
   of decimal places, THEN the function SHALL append the decimal separator
   followed by that many zero digits, exactly as before this change.
3. WHEN digit grouping is in effect for a `Decimal` value, THEN the function
   SHALL insert the thousands separator according to the grouping sizes,
   including for large integral decimals expressed in exponential source form,
   exactly as before this change.
4. WHEN a `Decimal` is formatted with no requested number of decimal places,
   THEN the function SHALL preserve the value's own fractional presentation, so
   that a `Decimal` carrying no fractional digits renders without a fractional
   part while a `Decimal` carrying explicit fractional digits renders them,
   exactly as before this change.
5. The system SHALL leave a `Decimal` whose magnitude is at least the smallest
   representable magnitude for the requested places unchanged, so that a value
   exactly equal to that smallest representable magnitude renders its own digits
   (for example, with two decimal places requested, such a value renders as
   `0.01`).

## Requirement 4: Leave non-Decimal inputs unaffected

**User story:** As a developer formatting integers, floats, and numeric strings,
I want their formatting to be identical to before, so that the small-decimal fix
is scoped only to `Decimal` values.

**Acceptance criteria**

1. The system SHALL apply the sub-precision zero adjustment of Requirement 1
   only to `Decimal` instances, and SHALL NOT apply it to integers, floats, or
   string inputs.
2. WHEN a float with no fractional part is formatted with no requested decimal
   places, THEN the function SHALL render it with a single trailing zero
   fractional digit, exactly as before this change.
3. WHEN an integer or numeric string is formatted, THEN the function SHALL
   apply the requested decimal-place padding, digit grouping, thousands
   separator, forced-grouping toggle, sign handling, and localization toggle
   exactly as before this change.
4. WHEN a very large integer is formatted with no requested decimal places,
   THEN the function SHALL render its full fixed-point digit string without
   truncation or exponential notation.
