# Requirements: Adopt a related object's primary key on save when the stored foreign-key value is empty

## Introduction

When a Django model instance holds a foreign-key relation (`ForeignKey` /
`OneToOneField`) to another model, the owning instance stores the related
object's primary key in the field's underlying attribute (the field's
`attname`, e.g. the `<field>_id` column). Separately, the cached related
object carries its own primary key.

If a related object is assigned to the owning instance *before* the related
object's primary key has been set, and the primary key is only defined
afterwards (then the related object is saved), the owning instance must pick up
the related object's now-known primary key when it is itself saved. This
matters especially when the related model's primary key is a non-numeric,
non-auto value (for example a `CharField` used as `primary_key=True`), whose
"unset" state is the empty string `''` rather than `None`.

The affected logic lives in `Model._prepare_related_fields_for_save` in
`django/db/models/base.py`, which is invoked from `Model.save()` /
`Model.save_base()` before the row is written. The goal is that a foreign-key
value that is still *empty* — whether that emptiness is represented as `None`
or as an empty scalar such as `''` — is (re)populated from the related
object's primary key, so the owning instance does not silently persist an empty
placeholder and lose the relationship. Previously only a `None` stored value
triggered this adoption, so a related model with an empty-string default
primary key was left referencing `''`.

## Requirement 1: Adopt the related object's primary key when the stored foreign-key value is empty

**User story:** As a developer saving a parent object whose related child was
attached before its primary key was assigned, I want the parent's foreign-key
value to be filled in from the child's primary key, so that the relationship is
persisted correctly instead of being lost to an empty placeholder.

**Acceptance criteria**

1. WHEN a model instance is saved and it has a cached foreign-key relation to a
   related object that already has a primary key, THEN the owning instance's
   stored foreign-key value SHALL be set to the related object's primary key
   whenever the currently stored foreign-key value is empty.
2. The system SHALL treat a stored foreign-key value as empty when it is any of
   the recognized empty values for the field — including the absent value
   (`None`) and an empty scalar such as the empty string `''`.
3. WHEN the stored foreign-key value is empty and is the empty string `''`
   while the related object's primary key is a non-numeric value (for example a
   string primary key), THEN the owning instance's stored foreign-key value
   SHALL become that non-numeric primary key rather than remaining the empty
   string.
4. IF the currently stored foreign-key value is non-empty (a present, non-empty
   scalar), THEN the system SHALL leave that stored foreign-key value unchanged
   and SHALL NOT overwrite it with the related object's primary key.
5. WHEN the owning instance is saved after the related object's primary key has
   been adopted, THEN a subsequent query filtering by the related object (or by
   the foreign-key value) SHALL match the saved row, and a query filtering the
   foreign-key value against the empty string SHALL NOT match it.

## Requirement 2: Preserve existing save-time related-field safeguards

**User story:** As a Django user relying on the existing save behavior for
related fields, I want the previously correct cases to keep working exactly as
before, so that fixing the empty-value case introduces no regression.

**Acceptance criteria**

1. WHEN a model instance is saved with a cached foreign-key relation to a
   related object that has not been saved and still has no primary key (its
   `pk` is `None`), THEN the system SHALL raise a `ValueError` reporting that
   the save is prohibited to prevent data loss due to the unsaved related
   object, naming the offending field.
2. WHEN such an unsaved, primary-keyless related object is detected on a
   single-valued (non-multiple) relation, THEN the system SHALL remove that
   object from the relation's cached value before raising.
3. WHEN a related object already has a primary key and the stored foreign-key
   value is already non-empty and equal to the related object's key, THEN the
   system SHALL preserve that stored value and complete the save normally.
4. WHEN, after resolving the stored foreign-key value, the related object's
   target key differs from the owning instance's stored foreign-key value, THEN
   the system SHALL clear the cached related object so a stale cached relation
   is not retained.
5. IF a foreign-key relation is not cached on the instance (no related object
   has been assigned), THEN the system SHALL skip this related-field processing
   for that field and leave the stored foreign-key value untouched.

## Requirement 3: Keep working for nullable foreign keys, custom target fields, and auto primary keys

**User story:** As a developer using nullable foreign keys, `to_field`
relations, and auto-increment primary keys, I want the save behavior to remain
correct for those cases, so that only the empty-value adoption is changed.

**Acceptance criteria**

1. WHEN a model instance with a nullable foreign key is saved after the related
   object has been saved and assigned its primary key, THEN the owning
   instance's stored foreign-key value SHALL be populated from the related
   object's primary key.
2. WHEN the foreign key references a non-primary target field (`to_field`),
   THEN the owning instance's stored foreign-key value SHALL be populated from
   the related object's corresponding target-field value using the same
   empty-value adoption rule.
3. WHEN the related object's primary key is an auto-generated numeric value that
   becomes available only after saving, THEN the owning instance's stored
   foreign-key value SHALL be populated from that numeric primary key on save.
4. The system SHALL NOT alter the stored foreign-key value of a relation whose
   cached related object matches the already-stored non-empty key, so that a
   correctly cached foreign key is not cleared by an ordinary save.
