# Requirements — django migration autodetector: dependencies for fields altered into relations

## Introduction

When Django's migration autodetector compares two project states and finds that
an existing model field has changed, it emits an `AlterField` operation. This
work happens in `MigrationAutodetector.generate_altered_fields`
(`django/db/migrations/autodetector.py`), which walks every field key present in
both the old and new state, and — for fields whose deconstruction differs and
that remain concrete-or-m2m (the "alter in place" branch) — builds an
`AlterField` operation and hands it to `self.add_operation(...)`.

The bug: when a plain, non-relational field (e.g. an `IntegerField` or a
`UUIDField`) is changed into a relation such as a `ForeignKey` that points at a
model in another app, the emitted `AlterField` operation carried **no migration
dependencies**. Because nothing told the migration graph that the referenced
app's model must already exist, applying the migration raised
`ValueError: Related model '<app>.<Model>' cannot be resolved.`

The goal is to make `generate_altered_fields` attach the relation-induced
ordering dependencies to the `AlterField` operation whenever the resulting field
is a relation, mirroring the dependency computation already used elsewhere for
newly added and created relations, so that the migration is ordered after the
migration that provides the referenced model. Fields that are not relations must
continue to produce `AlterField` operations with no relation dependencies, and
all other alter-field behavior must be preserved.

The affected module/function is
`django/db/migrations/autodetector.py::MigrationAutodetector.generate_altered_fields`,
which relies on the existing helper
`MigrationAutodetector._get_dependencies_for_foreign_key` to derive the
dependencies of a relational field.

## Requirement 1: An altered field that becomes a relation contributes its relation dependencies

**User story:** As a developer who changes a concrete field into a foreign key
pointing at a model in another app, I want the generated `AlterField` migration
to depend on the referenced app, so that running the migration does not fail
with "Related model cannot be resolved."

**Acceptance criteria**
1. WHEN `generate_altered_fields` emits an `AlterField` operation for a field
   whose new definition is a relation (its new field exposes a `remote_field`
   with a non-null related `model`), THEN `generate_altered_fields` SHALL pass a
   non-empty `dependencies` argument to `add_operation` for that operation.
2. WHEN the altered field's new definition points at a related model, THEN the
   operation's dependencies SHALL include a dependency identifying that related
   model's app label and object name, marked as a "creation" dependency (so the
   migration is ordered after the referenced model is created), computed exactly
   as `_get_dependencies_for_foreign_key` computes it for that field.
3. IF the altered field's new definition targets a swappable model
   (its `swappable_setting` is not `None`), THEN the operation's dependencies
   SHALL reference that setting (app label `"__setting__"` with the swappable
   setting name) instead of a concrete app/model, matching
   `_get_dependencies_for_foreign_key`.
4. IF the altered field's new definition has an explicit intermediary
   ("through") model that is not auto-created, THEN the operation's dependencies
   SHALL additionally include a creation dependency on that through model's app
   label and object name; WHEN the through model is auto-created or absent, THEN
   no such extra dependency SHALL be added.
5. The dependencies contributed for an altered relational field SHALL be exactly
   those returned by `_get_dependencies_for_foreign_key` for the new field —
   neither more nor fewer — so that an `AlterField` into a cross-app foreign key
   depends on the referenced app (resolvable to that app's latest migration by
   the dependency resolver), and nothing spurious is introduced.

## Requirement 2: Altered non-relational fields keep contributing no relation dependencies

**User story:** As a maintainer, I want ordinary field alterations (that do not
introduce a relation) to remain free of relation dependencies, so that existing
migration ordering and output are unchanged.

**Acceptance criteria**
1. WHEN `generate_altered_fields` emits an `AlterField` operation for a field
   whose new definition is not a relation (no `remote_field` related `model`),
   THEN that operation SHALL be emitted with no relation-derived dependencies.
2. The system SHALL compute the dependency list independently for each altered
   field within the iteration, so that a relational alteration for one field
   does not add dependencies to the `AlterField` operation of any other altered
   field.
3. WHILE altering a field that stays the same kind of field (both/neither
   many-to-many) and merely changes attributes such as nullability, default,
   regex/validators, or database column, `generate_altered_fields` SHALL
   continue to emit a single `AlterField` operation with the same
   `preserve_default` handling and questioner behavior as before, adding
   dependencies only when the new field is a relation.

## Requirement 3: Preserve all other altered-field behavior (regression protection)

**User story:** As a maintainer, I want the dependency change to be surgical, so
that no other autodetector behavior regresses.

**Acceptance criteria**
1. The system SHALL keep emitting a `RemoveField` followed by an `AddField`
   (instead of an `AlterField`) when a field changes between many-to-many and
   concrete, unaffected by the new dependency handling.
2. The system SHALL keep applying model-rename and field-rename adjustments to a
   relational field's target before computing its dependencies, so that a
   renamed related model or renamed target field is reflected in both the
   operation's field and its dependencies.
3. The system SHALL keep producing dependencies for newly **added** relational
   fields and for relations discovered during model **creation** and renames
   exactly as before; only the previously-missing dependencies for fields
   **altered** into relations are newly added.
4. WHEN a foreign key already existed on a field and only unrelated attributes of
   that relation change, THEN the emitted `AlterField` operation SHALL still
   carry that relation's dependencies (consistent with Requirement 1), so
   relational alterations remain correctly ordered.
5. The system SHALL preserve the number, type, and ordering of operations
   generated for all non-relational field alterations, foreign-key additions,
   and existing cross-app/same-app dependency scenarios that already worked.
