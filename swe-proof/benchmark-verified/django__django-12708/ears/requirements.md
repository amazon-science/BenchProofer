# Requirements: Removing an `index_together` must not fail when a `unique_together` covers the same fields

## Introduction

Django's schema-editing layer applies model changes to the database. When a
model's `index_together` option changes, the base schema editor
`BaseDatabaseSchemaEditor.alter_index_together`
(`django/db/backends/base/schema.py`) computes which composed indexes were
removed and, for each removed entry, delegates to the helper
`BaseDatabaseSchemaEditor._delete_composed_index` to locate and drop the single
database constraint that backs that index.

`_delete_composed_index` finds the constraint to drop by introspecting the
table's existing constraints and keeping those whose columns match the target
fields and whose properties match a set of filter flags supplied by the caller.
It then requires that **exactly one** constraint match; if it finds a different
number it raises `ValueError("Found wrong number (%s) of constraints ...")`.

The defect: on the supported backends, a multi-column `unique_together`
constraint is introspected as being *both* unique *and* index-backed. When a
model declares a `unique_together` and an `index_together` over the *same*
fields, removing the `index_together` used a filter that selected purely on
"is an index". That filter matched both the index constraint and the
unique constraint, so two constraints were found and the migration crashed with
the `ValueError` above, even though the user only intended to drop the index.

The goal is to make removal of an `index_together` succeed in this situation by
selecting only the ordinary (non-unique) index for deletion, leaving any
unique constraint over the same fields intact — without changing the existing
behavior for `index_together` and `unique_together` changes that do not overlap.

## Requirement 1: Dropping a removed composed index selects only the non-unique index

**User story:** As a developer running a migration that removes an
`index_together` from a model, I want the schema editor to drop the ordinary
backing index even when a `unique_together` exists over the same fields, so
that my migration applies successfully instead of crashing.

**Acceptance criteria**

1. WHEN `alter_index_together` processes a set of columns that was present in
   the old `index_together` but absent from the new one, THEN the schema editor
   SHALL restrict its search for the constraint to delete to constraints that
   are index-backed AND are NOT unique constraints.
2. IF the table has, over the same columns, both an ordinary index (from
   `index_together`) and a unique constraint (from `unique_together`), THEN
   removing the `index_together` SHALL identify exactly the ordinary index as
   the constraint to drop and SHALL NOT count the unique constraint as a match.
3. WHEN exactly one non-unique index-backed constraint matches the target
   columns, THEN the schema editor SHALL issue the statement that deletes that
   single index and SHALL complete without raising an error.
4. WHILE a unique constraint over the same columns exists, removing the
   overlapping `index_together` SHALL leave that unique constraint in place, so
   that after the operation the unique constraint over those columns still
   exists and the ordinary index over those columns no longer exists.

## Requirement 2: Preserve the exactly-one-constraint guard and unrelated behavior

**User story:** As a Django maintainer, I want the existing safety check and all
non-overlapping schema-alteration behavior to remain unchanged, so that the fix
introduces no regression.

**Acceptance criteria**

1. The schema editor SHALL continue to require that exactly one constraint match
   the target columns and filter flags when deleting a composed index or a
   composed unique constraint; IF the number of matching constraints is not
   exactly one, THEN it SHALL raise the same `ValueError` reporting the number of
   constraints found and the table and columns involved.
2. The system SHALL continue to exclude from the match any constraint or index
   that the model declares through its explicit `Meta.constraints` or
   `Meta.indexes` options.
3. WHEN adding a composed index for a set of columns newly present in
   `index_together`, THEN the schema editor SHALL create that index exactly as
   before, unaffected by this change.
4. WHEN altering `unique_together` (adding or removing a composed unique
   constraint), THEN the schema editor SHALL continue to select and drop the
   unique constraint using its existing unique-only filter, unaffected by this
   change.
5. WHEN removing an `index_together` for columns that have no overlapping unique
   constraint, THEN the schema editor SHALL drop the single matching index
   exactly as before.
6. The match SHALL continue to require that a candidate constraint's columns be
   exactly the target columns; a constraint covering a different set of columns
   SHALL NOT be selected for deletion.
