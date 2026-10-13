# Requirements: `floatformat` must preserve the exact value of Decimal inputs

## Introduction

The `floatformat` template filter (`django/template/defaultfilters.py`,
function `floatformat(text, arg=-1)`) renders a numeric value to a chosen number
of fractional places. Internally it first coerces the incoming value into a
working `decimal.Decimal`, then rounds and formats that decimal.

A defect exists in the coercion step: high-precision `Decimal` inputs lose
precision. When the incoming value is a `Decimal` carrying more significant
digits than a binary floating-point number can hold, the coercion routes the
value through a fixed-width binary floating-point approximation, so digits
beyond the float's precision are silently corrupted. For example, rendering
`Decimal('42.12345678901234567890')` with 20 fractional places produces
`42.12345678901234400000` instead of the exact input digits.

The goal is that the coercion preserve the **exact value** of an incoming exact
decimal number, so that a request for N fractional places can reproduce all N of
the input's digits — while leaving every other documented behavior of the filter
(float rounding, locale grouping, unlocalization, non-numeric handling, special
values, sign handling) unchanged.

## Requirement 1: Exact-value preservation for Decimal inputs

**User story:** As a template author displaying a high-precision `Decimal`
value, I want `floatformat` to keep every significant digit of that value, so
that the rendered number is exact and does not silently lose precision.

**Acceptance criteria**
1. WHEN `floatformat` receives a `decimal.Decimal` value, THEN the filter SHALL
   coerce it into a working decimal whose numeric value equals the input value
   exactly, retaining every significant digit regardless of how many there are.
2. WHEN the input is an exact decimal value, THEN the coercion SHALL NOT route
   that value through a binary floating-point approximation, and the rendered
   output SHALL NOT reflect any binary-float rounding error.
3. WHEN `floatformat` receives a `Decimal` value together with a positive
   fractional-place count that is at least the number of fractional digits the
   input carries, THEN the filter SHALL render every fractional digit of the
   input exactly, padding with trailing zeros only for places beyond the input's
   own digits.
4. IF the requested number of fractional places is smaller than the number of
   fractional digits the `Decimal` input carries, THEN the filter SHALL round
   the exact input value (round half up) to that many places rather than
   rounding a lossy approximation of it.

## Requirement 2: Preserve existing float formatting and rounding behavior

**User story:** As a template author using `floatformat` on ordinary float and
numeric-string inputs, I want the previous formatting and rounding results to
stay the same, so that the precision fix introduces no regressions.

**Acceptance criteria**
1. WHEN `floatformat` receives a float value and a fractional-place count, THEN
   the filter SHALL round to that many places using round-half-up and render the
   result exactly as the prior implementation did, so that ordinary float
   formatting is unchanged by the precision fix.
2. WHEN `floatformat` receives a `Decimal` value and a fractional-place count
   smaller than the number of fractional digits the value carries, THEN the
   filter SHALL round half up to that count.
3. WHEN a value has no fractional part to show under a negative or default
   place count, THEN the filter SHALL render it as an integer with no decimal
   point (dropping trailing fractional zeros).
4. WHEN `floatformat` receives an object that is not itself a float but exposes
   a float conversion, THEN the filter SHALL format the value obtained from that
   float conversion.
5. The system SHALL continue to accept the argument as either a positive count
   (always show exactly that many places), a negative count (show that many
   places only when a fractional part exists), or omitted (default of `-1`).

## Requirement 3: Preserve handling of invalid, non-numeric, and special inputs

**User story:** As a template author, I want malformed or special inputs handled
exactly as before, so that the fix does not change error or edge-case behavior.

**Acceptance criteria**
1. WHEN `floatformat` receives a value that cannot be interpreted as a number,
   THEN the filter SHALL return an empty string.
2. IF the argument cannot be interpreted as an integer place count, THEN the
   filter SHALL return the textual form of the input value unchanged, applying
   no rounding or place formatting.
3. WHEN the input value is positive or negative infinity or NaN, THEN the filter
   SHALL render the string representation of that special value.
4. WHEN the input value is zero, THEN the filter SHALL render zero with the
   requested number of fractional places without introducing a negative sign;
   and WHEN a negative value rounds to zero, THEN the filter SHALL NOT render a
   spurious `-0`.

## Requirement 4: Preserve locale grouping and unlocalization suffixes

**User story:** As a template author, I want the `g` (grouping) and `u`
(unlocalize) argument suffixes to keep working, so that formatting options are
unaffected by the fix.

**Acceptance criteria**
1. WHEN the argument ends with a `g` suffix, THEN the filter SHALL group the
   integer part by the active locale's thousand separator.
2. WHEN the argument ends with a `u` suffix, THEN the filter SHALL render the
   number unlocalized, using a period as the decimal separator regardless of the
   active locale.
3. The system SHALL accept the combined suffixes `gu` and `ug` and apply both
   grouping and unlocalization together.
4. The system SHALL treat a bare `g` or `u` suffix (with no leading digits) as
   the default place count.
