# Requirements: Upsert SQL must use database column names for conflict targets and updates

## Introduction

`QuerySet.bulk_create()` (in `django/db/models/query.py`) supports an upsert
mode: when called with `update_conflicts=True`, together with the
`update_fields` and `unique_fields` keyword arguments, it emits an
`INSERT ... ON CONFLICT ... DO UPDATE SET ...` statement so that rows which
collide on the conflict target are updated instead of raising an integrity
error. The conflict target is derived from `unique_fields`; the columns that get
overwritten are derived from `update_fields`.

Django models may configure an explicit database column name for a field (via
the field's `db_column` option) that differs from the Python field name — for
example a field named `sectorid` stored in a column named `SectorID`. The
`INSERT` portion of the statement already renders the real database column
names. However, the `ON CONFLICT (...)` target list and the
`DO UPDATE SET ... = EXCLUDED. ...` assignment list were rendered from the
Python field *names* instead of the database column names. When the two differ
(for instance when the column name uses mixed case), the produced SQL references
a column that does not exist and the database rejects the statement with a
"column does not exist" error.

The affected rendering happens in `SQLInsertCompiler.as_sql`
(`django/db/models/sql/compiler.py`), which calls the backend operation
`on_conflict_suffix_sql(...)` with the update-field and unique-field
information carried on the insert query. The goal is for the conflict-target and
update-assignment SQL to reference each participating field's actual database
column, so that upserts succeed for models whose fields declare a `db_column`,
while every existing upsert behavior and validation rule is preserved. Supporting
this requires `bulk_create()` to resolve the requested field names into the
model's field objects (so the database column of each is available) before the
statement is compiled.

## Requirement 1: Conflict target and update assignments use database column names

**User story:** As a developer performing an upsert with `bulk_create()` on a
model whose fields declare an explicit database column name, I want the emitted
`ON CONFLICT` statement to reference the real database columns, so that the
upsert executes successfully instead of failing with a "column does not exist"
error.

**Acceptance criteria**

1. WHEN `bulk_create()` is called with `update_conflicts=True`, a non-empty
   `update_fields`, and a non-empty `unique_fields`, THEN the emitted upsert
   statement SHALL identify the conflict target using the database column of each
   field listed in `unique_fields`, and SHALL identify each updated column using
   the database column of each field listed in `update_fields`.
2. WHEN a field participating in `unique_fields` or `update_fields` declares an
   explicit database column name that differs from its Python field name, THEN
   the conflict-target list and the update-assignment list SHALL use that
   declared database column name (not the field name), so that the generated SQL
   references a column that exists.
3. WHEN such an upsert targets a model with differing field-name/column-name
   fields and a conflicting row already exists, THEN the operation SHALL update
   the existing row's designated columns with the incoming values rather than
   inserting a duplicate, leaving the number of stored rows unchanged and each
   conflicting row's updated column set to the incoming value.
4. The value-insertion portion of the same statement SHALL continue to reference
   each column by its database column name, exactly as it did before, so the
   inserted-column list and the conflict/update column lists agree.

## Requirement 2: Resolve requested field names to model fields before compiling

**User story:** As a developer, I want the field names I pass in `update_fields`
and `unique_fields` to be resolved against the model's schema, so that the
upsert can obtain each field's database column and reject names that are not
valid fields.

**Acceptance criteria**

1. WHEN `bulk_create()` is called with a non-empty `unique_fields`, THEN each
   entry SHALL be resolved to the corresponding model field, and the special
   entry `"pk"` SHALL be resolved to the model's primary key field.
2. WHEN `bulk_create()` is called with a non-empty `update_fields`, THEN each
   entry SHALL be resolved to the corresponding model field.
3. IF any name supplied in `update_fields` or `unique_fields` does not correspond
   to a field on the model, THEN `bulk_create()` SHALL raise the same
   field-lookup error that resolving an unknown field name normally raises,
   rather than emitting SQL.
4. The resolution of requested names into field objects SHALL be performed by
   `bulk_create()` so that both the option validation and the downstream SQL
   compilation operate on resolved fields; the resolved field objects (carrying
   their database columns) SHALL be what is handed to the statement compiler for
   rendering the conflict target and update assignments.

## Requirement 3: Preserve upsert option validation (regression protection)

**User story:** As a maintainer, I want every existing validation rule for the
upsert options to keep firing exactly as before, so that misuse of
`bulk_create()` is still rejected with the established errors.

**Acceptance criteria**

1. WHEN `bulk_create()` is called with `update_conflicts=True` but without any
   `update_fields`, THEN it SHALL raise a `ValueError` reporting that the fields
   to update on conflict must be provided.
2. WHEN `bulk_create()` is called with `update_conflicts=True` and `update_fields`
   that include a non-concrete or many-to-many field, THEN it SHALL raise a
   `ValueError` reporting that only concrete fields may be used in
   `update_fields`.
3. WHEN `bulk_create()` is called with `update_conflicts=True` and `update_fields`
   that include the model's primary key, THEN it SHALL raise a `ValueError`
   reporting that primary keys may not be used in `update_fields`.
4. WHEN `bulk_create()` is called with `update_conflicts=True` and `unique_fields`
   that include a non-concrete or many-to-many field, THEN it SHALL raise a
   `ValueError` reporting that only concrete fields may be used in
   `unique_fields`.
5. WHEN `bulk_create()` is called with both `ignore_conflicts=True` and
   `update_conflicts=True`, THEN it SHALL raise a `ValueError` reporting that the
   two options are mutually exclusive.
6. IF the database backend supports specifying a conflict target and
   `update_conflicts=True` is requested without `unique_fields`, THEN
   `bulk_create()` SHALL raise a `ValueError` reporting that the unique fields
   triggering the upsert must be provided.

## Requirement 4: Preserve non-`db_column` upsert behavior (regression protection)

**User story:** As a maintainer, I want upserts on models whose fields have no
custom database column to behave exactly as before, so that the fix for
custom-column models does not change existing behavior.

**Acceptance criteria**

1. WHEN a field participating in `unique_fields` or `update_fields` has no custom
   database column (so its database column equals its Python field name), THEN
   the conflict-target and update-assignment SQL SHALL reference that same name,
   producing the identical statement it produced before this change.
2. WHEN an upsert is requested with a single unique field, a composite set of
   unique fields, or the primary key as the unique field, THEN the conflict
   target SHALL list exactly the database columns of those unique fields, and a
   conflicting insert SHALL update only the designated update columns and leave
   the stored row count unchanged.
3. The system SHALL continue to support the non-target upsert modes — ignoring
   conflicts, and updating conflicts on backends that do not require a specified
   conflict target — without regression from this change.
