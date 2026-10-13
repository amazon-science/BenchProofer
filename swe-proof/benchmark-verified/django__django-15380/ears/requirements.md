# Requirements: Detect a field rename in the same step a model is renamed

## Introduction

The migration autodetector (`django/db/migrations/autodetector.py`) compares a
prior project state (`from_state`) with a current project state (`to_state`)
and emits the migration operations needed to reconcile them. When a model has
been renamed, that fact is recorded in the autodetector's `renamed_models`
mapping, which sends a model's `(app_label, current_name)` key to the name the
same model carried in the prior state.

`AutodetectorTests`-level behavior aside, the specific routine at issue is
`Autodetector.generate_renamed_fields()`, which scans for fields that appear in
the current state but not the prior state and decides whether each is actually a
rename of an existing field. For every such candidate field it must locate the
state of the field's owning model in **both** snapshots.

The defect: when a model AND one of its fields are renamed in a single step,
`generate_renamed_fields()` looked up the owning model in the **current**
snapshot (`to_state.models`) using the model's **old** name. Because the model
was renamed this step, no entry exists under the old name in the current
snapshot, so the lookup raised `KeyError` and `makemigrations` crashed. This was
a regression introduced by an earlier refactor.

The goal is to locate each snapshot's owning-model state by the name the model
carries **in that snapshot** — the prior snapshot by the prior name, the current
snapshot by the current name — so that a simultaneous model-and-field rename is
detected without crashing, while every other rename-detection behavior is
preserved.

## Requirement 1: Locate the owning model in each snapshot by its name in that snapshot

**User story:** As a developer running `makemigrations` after renaming both a
model and one of its fields, I want the autodetector to correctly find the
model's definition in each snapshot, so that the tool does not crash.

**Acceptance criteria**
1. WHEN `generate_renamed_fields()` processes a candidate field whose key is
   `(app_label, model_name, field_name)`, THEN the routine SHALL determine the
   model's prior name as its current `model_name` translated back through the
   `renamed_models` mapping, falling back to `model_name` itself when the model
   was not renamed.
2. WHEN locating the owning model's state in the prior snapshot
   (`from_state.models`), THEN the routine SHALL index that snapshot by the
   model's **prior** name (`app_label`, prior name).
3. WHEN locating the owning model's state in the current snapshot
   (`to_state.models`), THEN the routine SHALL index that snapshot by the
   model's **current** name (`app_label`, `model_name`).
4. IF a model and one or more of its fields are renamed in a single step, THEN
   `generate_renamed_fields()` SHALL locate both snapshot states without raising
   `KeyError` (or any other exception).
5. WHEN the current-snapshot model state has been located, THEN the candidate
   field SHALL be retrieved from that current-snapshot state (so the field being
   examined is the one under its new name in the current model).

## Requirement 2: Emit both the model rename and the field rename in one migration

**User story:** As a developer, I want a single-step rename of a model together
with one of its fields to produce the two corresponding rename operations, so
that the generated migration matches what I actually changed.

**Acceptance criteria**
1. WHEN the autodetector runs against a state in which exactly one model has been
   renamed and exactly one of that model's fields has been renamed (with the
   questioner confirming both a model rename and a field rename), THEN it SHALL
   produce a single migration for the affected app.
2. WHEN that migration is produced, THEN it SHALL contain a model-rename
   operation followed by a field-rename operation, in that order.
3. WHEN the model-rename operation is produced, THEN its old name SHALL be the
   model's prior name and its new name SHALL be the model's current name.
4. WHEN the field-rename operation is produced, THEN its old name SHALL be the
   field's prior name and its new name SHALL be the field's current name.
5. The field-rename detection SHALL compare the candidate current field against
   the removed prior field using the model's prior-snapshot definition, so that
   the field is recognized as a rename rather than being treated as a drop plus
   an add.

## Requirement 3: Preserve existing rename-detection and change-detection behavior

**User story:** As a maintainer, I want the fix to be surgical, so that all
previously working autodetection continues to behave exactly as before.

**Acceptance criteria**
1. The autodetector SHALL keep detecting a field rename that occurs **without** a
   simultaneous model rename, producing the field-rename operation with the
   correct old and new names.
2. The autodetector SHALL keep detecting a model rename that occurs **without**
   any field rename, producing the model-rename operation with the correct old
   and new names.
3. WHEN a field is renamed and its database column is set to preserve the old
   column name, THEN the autodetector SHALL keep emitting the same operations it
   previously did to preserve the underlying column.
4. The autodetector SHALL keep treating model names case-insensitively, so that a
   change that only alters the case of a model name produces no migration.
5. The autodetector SHALL keep correctly handling renamed models that are
   referenced by foreign-key and many-to-many relations from other models.
6. The autodetector SHALL keep producing, for all other unchanged detection
   scenarios (new/removed/altered models and fields, index and constraint
   changes, option changes, dependency ordering, and migration name
   suggestions), the same operations and ordering as before this change.
