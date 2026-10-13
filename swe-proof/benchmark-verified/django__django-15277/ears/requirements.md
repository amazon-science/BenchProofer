# Requirements: Don't attach an unusable length validator to a max-length-less CharField

## Introduction

When a query expression wraps a raw Python value (for example
`annotate(x=Value('test'))`), Django infers a database field type for that value
through `Value._resolve_output_field` in `django/db/models/expressions.py`. For a
string value this returns a bare `fields.CharField()` — constructed with no
`max_length` argument, so its `max_length` attribute is `None`.

`CharField.__init__` in `django/db/models/fields/__init__.py` unconditionally
appended a `MaxLengthValidator` built from `self.max_length`. When `max_length`
is `None`, that validator is inoperable: invoking it (e.g. via the field's
`clean()`/`run_validators()` path) compares a value's length against `None` and
raises `TypeError: '>' not supported between instances of 'int' and 'NoneType'`.
The validator is also pointless in this context because output fields inferred
for `Value` are never run through model validation.

The goal is to make `CharField` append the length validator only when an actual
maximum length is declared — matching the existing precedent in
`BinaryField.__init__` — so that a `max_length`-less `CharField` (such as the
one produced for a string `Value`) carries no broken validator and can be
cleaned without error, while every existing behavior (length enforcement when a
maximum is set, the system check that model `CharField`s must declare a maximum,
and all other expression/field behavior) is preserved.

## Requirement 1: Only attach a length validator when a maximum length is declared

**User story:** As a developer using Django's ORM, I want a `CharField` that has
no declared maximum length to be constructed without an unusable length
validator, so that fields inferred for expressions can be validated/cleaned
without raising a spurious error.

**Acceptance criteria**

1. WHEN a `CharField` is instantiated with `max_length` equal to `None` (its
   default when no maximum is supplied), THEN `CharField.__init__` SHALL NOT add
   a maximum-length validator to the field's `validators`.
2. WHEN a `CharField` is instantiated with a non-`None` `max_length`, THEN
   `CharField.__init__` SHALL append a maximum-length validator that enforces
   that declared bound, exactly as before.
3. The system SHALL preserve, in order, any validators already present on the
   field (from the field type or supplied explicitly) and only append the
   length validator in the case where a maximum length is declared.
4. IF a `CharField` has `max_length` equal to `None`, THEN running the field's
   validation path (`run_validators`/`clean`) over a value SHALL NOT raise a
   `TypeError` arising from comparing a length against `None`.

## Requirement 2: Output fields inferred for `Value` can be cleaned without error

**User story:** As a developer wrapping literals in `Value(...)`, I want the
output field resolved for that value to be usable, so that instantiating and
cleaning it does not blow up even though such output fields are not normally run
through validation.

**Acceptance criteria**

1. WHEN `Value._resolve_output_field` is called for a string value, THEN it
   SHALL return a `CharField` whose `max_length` is `None` and whose
   `validators` contain no maximum-length validator.
2. WHEN the output field resolved for a string `Value` is asked to clean that
   string value with no model instance, THEN it SHALL return the cleaned value
   WITHOUT raising an exception.
3. WHEN `Value._resolve_output_field` resolves the output field for a supported
   literal value, THEN cleaning that resolved field over its own value with no
   model instance SHALL complete WITHOUT raising an exception — for the string
   case because the length validator is no longer attached, and for any other
   literal type because this change leaves its resolved field unaffected.
4. The system SHALL continue to map each supported literal handled by
   `Value._resolve_output_field` to the same corresponding field type as before
   (e.g. a string to a `CharField`), changing only whether a length validator is
   attached.

## Requirement 3: Preserve existing field, check, and expression behavior

**User story:** As a maintainer, I want the change to be strictly additive in
behavior, so that no existing length enforcement, system check, or expression
semantics regress.

**Acceptance criteria**

1. WHEN a value longer than a declared, non-`None` `max_length` is validated by a
   `CharField` carrying its length validator, THEN validation SHALL still fail as
   it did before the change.
2. WHEN Django's system checks run against a model `CharField` that declares no
   `max_length`, THEN the check framework SHALL still report the existing error
   requiring a `max_length` attribute; omitting the length validator SHALL NOT
   suppress that check.
3. The system SHALL keep `BinaryField` construction behavior unchanged, appending
   its maximum-length validator only when a non-`None` `max_length` is declared.
4. The system SHALL preserve all other `Value` and expression behaviors —
   including equality, hashing, deconstruction, `repr`, output-field resolution
   (including the explicit-output-field and decimal cases), and SQL compilation —
   unchanged by this modification.
