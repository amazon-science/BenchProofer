# Requirements: Uniform validation error for undecodable DecimalField values

## Introduction

`DecimalField` (in `django/db/models/fields/__init__.py`) converts an arbitrary
input value into a decimal number through its `to_python(value)` method. This
method is invoked during field cleaning/validation (e.g. `Field.clean(value,
model_instance)`), during query preparation (`get_prep_value`), and when saving
model instances, so the value it receives may be anything a caller assigned to
the field.

The conversion has a fixed precedence: a value of `None` passes straight
through; a `float` is converted using the field's decimal context (honoring
`max_digits` precision and the default `ROUND_HALF_EVEN` rounding); any other
value is interpreted as a `Decimal`.

The problem is that this last interpretation can fail in several low-level ways
depending on the offending value. A value that merely looks number-like but is
malformed (e.g. a non-numeric string) is already reported as a
`ValidationError`, but values whose type has no decimal interpretation at all —
for example a `dict` assigned to the field by mistake, or any other non-numeric
object or container — let the underlying failure escape as a raw `TypeError` (or
`ValueError`). As the issue describes, assigning a dictionary to a decimal field
by mistake surfaces an opaque `TypeError` instead of a field-level
`ValidationError`, which makes it hard to trace the problem back to the specific
field on a model with many fields.

The goal is to make `DecimalField.to_python()` report **every** low-level
failure of the value→decimal interpretation uniformly, as the same
`ValidationError`, so callers never have to discriminate among the assorted
low-level failure modes — while leaving the successful and pass-through cases
(including `None`, floats, integers, and numeric strings) unchanged.

## Requirement 1: Any undecodable value yields a uniform ValidationError

**User story:** As a developer who may assign an inappropriate value to a
decimal field, I want a single, predictable field-level validation error for any
value that cannot be interpreted as a decimal number, so that I can trace the
problem to the field regardless of the value's type.

**Acceptance criteria**

1. WHEN `DecimalField.to_python(value)` is given a value that is neither `None`
   nor a `float` and that cannot be interpreted as a decimal number, THEN it
   SHALL raise a `django.core.exceptions.ValidationError`.
2. WHEN such an undecodable value is supplied, THEN the raised error SHALL use
   error code `'invalid'` and SHALL carry the field's configured "invalid"
   error message, with the offending value exposed as the message's `value`
   parameter so the rendered message reports that value.
3. IF the low-level attempt to interpret the value as a decimal fails because
   the value's type has no decimal interpretation (for instance a non-numeric
   object or container passed where a number was expected), THEN
   `to_python` SHALL raise the same `ValidationError` and SHALL NOT let a
   `TypeError` (or any other low-level exception) propagate to the caller.
4. IF the value is a textual value (a string, or a byte-string) whose contents
   are not a well-formed decimal literal, THEN `to_python` SHALL raise the same
   `ValidationError` rather than letting a low-level conversion error propagate.
5. WHEN a decimal field cleans an undecodable value through
   `Field.clean(value, model_instance)`, THEN the resulting validation error
   SHALL be a `ValidationError` whose message identifies the offending value,
   for each such value regardless of its type.

## Requirement 2: Valid and pass-through values are unaffected

**User story:** As a developer using decimal fields with legitimate values, I
want the successful conversions to keep behaving exactly as before, so that
broadening the error handling does not change correct results.

**Acceptance criteria**

1. WHEN `to_python(None)` is called, THEN it SHALL return `None`.
2. WHEN `to_python` is given a `float`, THEN it SHALL convert the value using the
   field's decimal context, honoring `max_digits` as the precision and applying
   the default `ROUND_HALF_EVEN` rounding (e.g. converting under a field of
   `max_digits=4, decimal_places=2` yields three significant digits).
3. WHEN `to_python` is given an integer or a numeric string that represents a
   valid decimal, THEN it SHALL return the corresponding `Decimal` value without
   raising.
4. The system SHALL preserve trailing zeros in the fractional part of a decimal
   value rather than truncating them.
5. WHEN `get_prep_value(None)` is called on a decimal field, THEN it SHALL return
   `None`; WHEN `get_prep_value` is given a numeric string, THEN it SHALL return
   the equivalent `Decimal`.
6. The system SHALL continue to return a field's configured default decimal value
   from `get_default()` unchanged.

## Requirement 3: Numeric values remain usable in queries

**User story:** As a developer filtering on a decimal field, I want numeric
values to be usable in a lookup without the conversion crashing, so that queries
succeed regardless of the magnitude of the value.

**Acceptance criteria**

1. WHEN a decimal field prepares an integer value for use in a query lookup,
   THEN the conversion SHALL succeed and SHALL NOT raise, including for integers
   too large to fit within the field's declared precision.
2. WHEN a queryset filters a decimal field against an integer value, THEN
   building that filter SHALL NOT crash.
3. WHEN a decimal field is filtered using a numeric string value, THEN the filter
   SHALL match rows whose stored decimal equals that value.

## Requirement 4: Range validation is preserved

**User story:** As a maintainer, I want the existing digit-count validation to
keep rejecting out-of-range decimals, so that broadening `to_python`'s error
handling does not weaken field validation.

**Acceptance criteria**

1. WHEN a decimal field cleans a value whose total number of digits exceeds the
   field's `max_digits`, THEN cleaning SHALL raise a `ValidationError` reporting
   the maximum number of digits allowed.
2. WHEN a decimal field cleans a value whose number of decimal places exceeds the
   field's `decimal_places`, THEN cleaning SHALL raise a `ValidationError`
   reporting the maximum number of decimal places allowed.
3. WHEN a decimal field cleans a value whose number of whole (integer-part)
   digits exceeds the allowed maximum, THEN cleaning SHALL raise a
   `ValidationError` reporting the maximum number of whole digits allowed.
4. The system SHALL continue to persist and retrieve valid decimal values
   without corrupting them through an intermediate floating-point conversion.
