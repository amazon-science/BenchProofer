# Requirements: Foreign key value validation should consult the unfiltered stored records

## Introduction

When a model instance is validated, each foreign key field checks that the value
it holds actually refers to an existing target record. This existence check is
performed by the `validate()` method of the foreign key field in
`django/db/models/fields/related.py` (the `ForeignKey` / related-field class).

The target model can expose more than one view of its rows:

- its **default manager** (`_default_manager`), which the target model may narrow
  with a custom manager whose `get_queryset()` applies a standing filter, so that
  some genuinely stored rows are hidden from the default view (for example rows
  flagged as archived/retired); and
- its **base manager** (`_base_manager`), which presents every stored row of the
  target model regardless of any such custom default filtering.

Previously the field's `validate()` built its existence query from the target
model's default manager. As a result, a value that refers to a real, stored
target row was rejected as non-existent whenever that row was hidden by the
default manager's filter — even though a form or caller had deliberately offered
that row as a valid choice. The user-facing effect was a spurious "instance with
id N does not exist" validation error for rows that do exist.

The goal is for foreign key existence validation to depend only on whether an
eligible target row genuinely exists, never on whether the target model's default
manager happens to hide it, while preserving all other validation behavior
(early exits, the choice constraint, the database routing, and the error raised
when no matching row exists).

## Requirement 1: Validate foreign key existence against the unfiltered stored records

**User story:** As a developer whose target model has a custom default manager
that filters out some rows, I want foreign key validation to accept a value that
points at any genuinely stored row, so that a form or caller can legitimately
offer those otherwise-hidden rows as valid choices.

**Acceptance criteria**

1. WHEN a foreign key field validates a non-null value against a target model,
   THEN the field SHALL determine existence using the target model's base
   manager (the manager that exposes every stored row) rather than the target
   model's default manager.
2. IF the target model defines a custom default manager whose queryset hides some
   stored rows, THEN validation SHALL accept a foreign key value that refers to
   an existing target row even when that row is hidden by the default manager's
   filter.
3. WHEN validating a foreign key value, THEN the field SHALL restrict the
   existence query to target rows whose referenced field equals the value being
   validated.
4. WHEN validating a foreign key value, THEN the field SHALL additionally apply
   the field's standing choice constraint (`limit_choices_to`) to the existence
   query, so that only rows satisfying that constraint count as a match.
5. IF at least one stored target row satisfies both the referenced-field match
   and the choice constraint, THEN validation SHALL succeed (raise no error).

## Requirement 2: Reject a value with no matching stored record

**User story:** As a developer relying on referential integrity, I want a foreign
key value that matches no eligible stored target row to still be rejected, so
that invalid references are caught.

**Acceptance criteria**

1. IF no stored target row matches both the referenced-field value and the choice
   constraint, THEN the field SHALL raise a validation error.
2. WHEN raising this validation error, THEN the field SHALL use the field's
   existing "invalid" error message and its error code `invalid`.
3. WHEN raising this validation error, THEN the error SHALL carry parameters
   identifying the target model, the referenced field name, and the offending
   value (including a `pk` entry for backwards compatibility), exactly as before
   this change.

## Requirement 3: Preserve the existing early-exit and routing behavior

**User story:** As a maintainer, I want the change to be confined to which manager
supplies the existence query, so that every other aspect of foreign key
validation continues to behave as it did.

**Acceptance criteria**

1. IF the foreign key is a parent-link field, THEN the field SHALL return without
   performing any existence check.
2. IF the value being validated is `None`, THEN the field SHALL return without
   performing any existence check (after the base field validation).
3. The field SHALL continue to run the inherited base field validation before the
   existence check.
4. WHEN building the existence query, THEN the field SHALL continue to select the
   read database via the database router (`db_for_read`) using the model instance
   being validated, so multi-database routing is unchanged.
5. The system SHALL keep validating ordinary foreign keys correctly: a value that
   matches an eligible stored target row SHALL pass, and a value that matches no
   stored target row SHALL fail, for target models that use the standard default
   manager (where the base and default views coincide).
