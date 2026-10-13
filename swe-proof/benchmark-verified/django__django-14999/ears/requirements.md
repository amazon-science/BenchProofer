# RenameModel with an unchanged database table must be a no-op

## Introduction

Django's migration framework represents a model rename as the
`RenameModel` operation in `django/db/migrations/operations/models.py`.
When such an operation is applied to the database, its
`database_forwards` method asks the schema editor to rename the model's
main table and to update every dependent object (foreign keys pointing
at the model, and auto-created many-to-many tables and columns derived
from the model name). The `database_backwards` method performs the same
work in reverse by swapping the old/new names and delegating to
`database_forwards`.

A model can pin an explicit table name through its `Meta.db_table`
option. When a model is renamed but its `db_table` is set to a fixed
value, the stored table name does not actually change — only the Python
class name does. In that situation the current implementation still
issues schema-editor operations, which on PostgreSQL drops and recreates
foreign-key constraints and on SQLite rebuilds the table. This work is
unnecessary and harmful: renaming the model has no effect on the
physical schema.

The goal is that a `RenameModel` operation whose effective database
table name is unchanged performs no database work at all — in either
direction — while every rename that *does* change the table name (or
its dependent tables/columns) continues to behave exactly as before.

## Requirement 1: A rename that does not change the table name issues no database operations

**User story:** As a Django developer who has renamed a model that pins
its table name with `Meta.db_table`, I want applying the migration to
touch nothing in the database, so that my existing foreign-key
constraints and table are left intact.

**Acceptance criteria**

1. WHEN `RenameModel.database_forwards` runs for a model whose stored
   database table name before the rename equals the stored database
   table name after the rename, THEN the operation SHALL emit no
   schema-editor work — no table rename, no dependent foreign-key
   update, and no many-to-many table or column change — resulting in
   zero database queries being executed.
2. WHEN `RenameModel.database_backwards` runs for a model whose stored
   database table name is the same before and after the reverse rename,
   THEN the operation SHALL likewise emit no schema-editor work and
   execute zero database queries.
3. The system SHALL determine "unchanged" by comparing the resolved
   database table name of the model in the source state against the
   resolved database table name of the model in the target state (the
   value exposed by the model's metadata as its database table), not by
   comparing the model class names.
4. WHEN the table name is unchanged, THEN the operation SHALL return
   without contacting the database, and the state of the schema (tables,
   columns, and constraints) SHALL be left exactly as it was.

## Requirement 2: A rename that changes the table name keeps its full existing behavior

**User story:** As a Django developer renaming a model that does not pin
its table name, I want the migration to rename the underlying table and
fix up everything that references it, so that renames keep working as
they always have.

**Acceptance criteria**

1. WHEN `RenameModel.database_forwards` runs for an applicable model
   whose stored database table name before the rename differs from the
   name after the rename, THEN the operation SHALL instruct the schema
   editor to rename the model's main table from the old table name to
   the new table name.
2. WHEN the main table is renamed, THEN the operation SHALL also update
   every related object whose field points at the renamed model so that
   those foreign-key references target the new table, preserving the
   existing dependent-field handling.
3. WHEN the renamed model owns auto-created many-to-many tables whose
   names derive from the model name, THEN the operation SHALL rename
   those many-to-many tables and rename the column in each that is based
   on the model name, exactly as before, and SHALL skip self-referential
   many-to-many fields and non-auto-created through tables.
4. IF the operation is not applicable to the current database connection
   (the migration is not allowed for this model on this connection),
   THEN the operation SHALL emit no schema-editor work regardless of
   whether the table name changed.
5. The system SHALL preserve the relative order of the emitted work when
   the table name changes: the main table rename first, followed by the
   dependent follow-up operations.

## Requirement 3: Reverse migrations remain consistent with forward migrations

**User story:** As a Django developer rolling a migration back, I want
the reverse of a `RenameModel` to mirror the forward operation, so that
applying and un-applying a rename is symmetric.

**Acceptance criteria**

1. WHEN `RenameModel.database_backwards` runs, THEN it SHALL carry out
   the reverse rename by exchanging the old and new names and performing
   the same behavior specified for `database_forwards`, so that the
   no-op condition in Requirement 1 and the full-rename behavior in
   Requirement 2 apply identically in the reverse direction.
2. The system SHALL leave the operation's stored old/new name attributes
   unchanged after `database_backwards` completes.
