# Relation-agnostic field normalization in the migration autodetector

## Introduction

The Django migration autodetector compares model states to detect changes such
as renamed models. As part of this comparison it normalizes each model field
into a *relation-agnostic* form so that fields which point at another model can
be compared without regard to which model they actually target (the target can
legitimately change during a rename).

This normalization lives in
`django.db.migrations.autodetector.MigrationAutodetector.only_relation_agnostic_fields`.
For each field it computes a deconstruction — a triple of an import path, a list
of positional arguments, and a keyword mapping — via `deep_deconstruct`. For a
field that relates to another model, the entry recording the target model is
supposed to be removed from that keyword mapping so it does not influence rename
detection.

The current implementation assumes that a related field's deconstructed keyword
mapping always contains the target entry and removes it unconditionally. A
legitimately-designed custom related field may hardcode its target and omit that
entry from its own deconstruction. In that case the normalization crashes with a
`KeyError` while trying to remove an absent entry, which aborts change
detection entirely (for example during `makemigrations`/`migrate` and test
database setup). The goal is to make the removal tolerant of an already-absent
target entry while preserving the normalization behavior for every other field.

## Requirement 1: Tolerate related fields whose deconstruction omits the target entry

**User story:** As a developer using a custom related field that hardcodes its
target model and drops the target entry from its own deconstruction, I want the
migration autodetector to normalize my model's fields without crashing, so that
migration change detection, `makemigrations`, `migrate`, and test-database
setup complete successfully.

**Acceptance criteria**

1. WHEN `only_relation_agnostic_fields` normalizes a field that points at
   another model but whose deconstructed keyword mapping does NOT contain the
   target-model entry, THEN the method SHALL complete without raising an error
   and SHALL carry that field's keyword mapping over unchanged (nothing to
   remove).
2. IF normalization is invoked on a model that contains such a related field,
   THEN the overall change detection SHALL run to completion and produce its
   normal result rather than aborting with a `KeyError`.
3. WHEN a new model containing such a hardcoded-target related field is added
   between two project states, THEN change detection SHALL report exactly the
   migration(s) required to create that model (a single create-model change for
   the added model), with no error surfaced to the caller.

## Requirement 2: Preserve target removal for related fields that do record a target

**User story:** As a maintainer of the autodetector, I want related fields that
DO record their target to keep being made target-agnostic exactly as before, so
that rename detection continues to work.

**Acceptance criteria**

1. WHEN `only_relation_agnostic_fields` normalizes a field that points at
   another model and whose deconstructed keyword mapping DOES contain the
   target-model entry, THEN that entry SHALL be removed from the field's keyword
   mapping in the produced normalization.
2. The system SHALL leave the field's import path, its positional arguments, and
   every keyword entry other than the target entry unchanged when producing the
   normalized deconstruction of a related field.

## Requirement 3: Preserve normalization of non-relational fields and result shape

**User story:** As a maintainer of the autodetector, I want fields that do not
point at another model, and the overall structure of the result, to be
unaffected by this change, so that no other change-detection behavior regresses.

**Acceptance criteria**

1. WHEN `only_relation_agnostic_fields` normalizes a field that does NOT point at
   another model, THEN that field's deconstruction SHALL be carried over verbatim
   (path, positional arguments, and full keyword mapping all unchanged).
2. The system SHALL visit the model's fields in their given (sorted) order and
   SHALL collect one normalized deconstruction per field, preserving order and
   without dropping, duplicating, or reordering fields.
3. The system SHALL continue to remove the target entry only for fields that
   point at another model, and SHALL never remove it for non-relational fields.
