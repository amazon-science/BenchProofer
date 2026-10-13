# Requirements: Customizable error code on constraint validation errors

## Introduction

Django's model constraints already let a developer customize the human-readable
message of the `ValidationError` raised when a constraint is violated (the
`violation_error_message` constructor argument on `BaseConstraint` and its
subclasses). There is currently no way to customize the machine-readable *code*
carried by that same `ValidationError`, even though Django's documentation
recommends providing a descriptive error code when raising validation errors.

This change adds an optional error-code setting to the constraint classes in
`django/db/models/constraints.py` — `BaseConstraint`, `CheckConstraint`,
`UniqueConstraint` — and to `ExclusionConstraint` in
`django/contrib/postgres/constraints.py`. The setting is a new optional
keyword argument `violation_error_code`, mirroring the existing
`violation_error_message` argument. When configured, the code must be:

* stored on the constraint and default to unset (no code) when not supplied;
* surfaced on the `ValidationError.code` raised by `validate(...)`;
* included in the object's reconstruction (deconstruction) data;
* reflected in the object's `repr()`;
* accounted for in equality comparisons.

The goal is behavioral parity with `violation_error_message`, plus the specific
validation semantics the affected constraints already exhibit. All previously
supported behavior of these classes must be preserved.

## Requirement 1: Configure and store an optional violation error code

**User story:** As a developer defining a constraint, I want to pass an optional
error code so that the `ValidationError` raised on violation carries a
descriptive, machine-readable code.

**Acceptance criteria**

1. The system SHALL accept an optional keyword argument `violation_error_code`
   on the constructor of `BaseConstraint`, `CheckConstraint`, `UniqueConstraint`
   (in `django/db/models/constraints.py`), and `ExclusionConstraint` (in
   `django/contrib/postgres/constraints.py`).
2. WHEN a constraint is created with `violation_error_code` set to a value,
   THEN the constraint SHALL expose that value through an attribute named
   `violation_error_code`.
3. WHEN a constraint is created without supplying `violation_error_code`,
   THEN the constraint's `violation_error_code` attribute SHALL be `None`.
4. The subclasses `CheckConstraint`, `UniqueConstraint`, and
   `ExclusionConstraint` SHALL forward a supplied `violation_error_code` to the
   base initialization so that it is stored identically to how it is stored on
   `BaseConstraint`.
5. IF `violation_error_code` is supplied, THEN adding it SHALL NOT change how
   `violation_error_message` is accepted, stored, or defaulted.

## Requirement 2: Surface the code on the raised validation error

**User story:** As a developer relying on error codes, I want the constraint's
`validate(...)` to raise a `ValidationError` whose `code` equals my configured
code, so that downstream handling can key off it.

**Acceptance criteria**

1. WHEN `CheckConstraint.validate(...)` detects that the check is not satisfied
   for the candidate instance, THEN it SHALL raise a `ValidationError` whose
   `code` equals the constraint's configured `violation_error_code`.
2. WHEN `UniqueConstraint.validate(...)` detects a violation for a constraint
   defined with a condition, THEN it SHALL raise a `ValidationError` whose
   `code` equals the constraint's configured `violation_error_code`.
3. WHEN `ExclusionConstraint.validate(...)` detects a violation, THEN it SHALL
   raise a `ValidationError` whose `code` equals the constraint's configured
   `violation_error_code`, both for the unconditional case and for the case
   where the constraint has a condition.
4. IF a constraint has no configured code (`violation_error_code` is `None`),
   THEN a `ValidationError` raised on violation SHALL carry `code` equal to
   `None`.
5. WHEN a constraint's `validate(...)` detects no violation for the candidate
   instance, THEN it SHALL NOT raise a `ValidationError`.
6. The system SHALL leave the human-readable message of every raised
   `ValidationError` unchanged from its prior behavior (the configured or
   default `violation_error_message`), independent of the code.

## Requirement 3: Preserve the field-based unique-constraint violation semantics

**User story:** As a developer using a `UniqueConstraint` defined over plain
fields, I want the existing "…already exists" behavior preserved so that legacy
model validation keeps working.

**Acceptance criteria**

1. WHEN `UniqueConstraint.validate(...)` detects a violation for a constraint
   defined by fields (no expressions and no condition), THEN it SHALL raise a
   `ValidationError` built from the model's existing unique-error message for
   those fields (the same message and code the model would produce for that set
   of fields during its own uniqueness validation).
2. WHILE handling that field-based unique violation, the raised
   `ValidationError`'s `code` SHALL be the model-derived unique-error code for
   the constrained fields — `"unique"` when the constraint covers a single
   field and `"unique_together"` when it covers multiple fields — and SHALL NOT
   be replaced by any configured `violation_error_code`.
3. WHILE handling that field-based unique violation, the raised
   `ValidationError`'s message SHALL be the model-derived unique-error message
   for the constrained fields (a single-field "…already exists" message for one
   field, or the combined-fields message for multiple fields) and SHALL NOT be
   replaced by any configured `violation_error_message`.
4. The system SHALL continue to skip validation (raise nothing) when a
   constrained field value is `None` (or an empty string treated as null),
   exactly as before.

## Requirement 4: Include the code in reconstruction (deconstruction) data

**User story:** As a developer relying on migrations and serialization, I want
the configured code to round-trip so that a reconstructed constraint is
equivalent to the original.

**Acceptance criteria**

1. WHEN a constraint is deconstructed and a `violation_error_code` is
   configured (not `None`), THEN the returned keyword arguments SHALL include a
   `violation_error_code` entry equal to the configured value.
2. WHEN a constraint is deconstructed and no `violation_error_code` is
   configured, THEN the returned keyword arguments SHALL NOT include a
   `violation_error_code` entry.
3. The system SHALL continue to include `violation_error_message` in the
   deconstruction keyword arguments only under its existing condition (set and
   different from the default), unaffected by the code.
4. The system SHALL preserve every other existing entry of the deconstruction
   result (path, positional arguments, and all other keyword arguments) for
   each constraint class.

## Requirement 5: Reflect the code in equality comparisons

**User story:** As a developer comparing constraints, I want the code to
participate in equality so that constraints differing only by code are treated
as different.

**Acceptance criteria**

1. WHEN two constraints of the same class are compared for equality and they
   agree on all previously compared attributes, THEN they SHALL be considered
   equal only if their `violation_error_code` values are also equal.
2. IF two otherwise-identical constraints of the same class have different
   `violation_error_code` values, THEN they SHALL be considered not equal.
3. WHEN two otherwise-identical constraints of the same class have the same
   `violation_error_code` value (including both being `None`), THEN they SHALL
   be considered equal.
4. This equality behavior SHALL apply to `CheckConstraint`,
   `UniqueConstraint`, and `ExclusionConstraint`, in each case in addition to
   the attributes those classes already compared.

## Requirement 6: Reflect the code in the textual representation

**User story:** As a developer inspecting constraints, I want `repr()` to show
the configured code so that debugging output is informative.

**Acceptance criteria**

1. WHEN a constraint with a configured `violation_error_code` is represented as
   a string via `repr()`, THEN the representation SHALL include a
   ` violation_error_code=<repr-of-code>` segment.
2. WHEN a constraint has no configured `violation_error_code`, THEN its `repr()`
   SHALL NOT include any `violation_error_code` segment.
3. For `CheckConstraint`, `UniqueConstraint`, and `ExclusionConstraint`, the
   code segment SHALL appear immediately before the existing
   `violation_error_message` segment, and the representation SHALL otherwise be
   unchanged from its prior form.
4. The system SHALL continue to include the `violation_error_message` segment
   in `repr()` only under its existing condition (set and different from the
   default), unaffected by the code.
