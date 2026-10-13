# Requirements: Adding a nullable unique/one-to-one field on SQLite

## Introduction

Django's SQLite database backend implements schema changes through a schema
editor. When a new field is added to an existing model, the SQLite schema
editor (`django.db.backends.sqlite3.schema.DatabaseSchemaEditor.add_field`)
must choose between two strategies:

1. Emitting a plain `ALTER TABLE ... ADD COLUMN` statement (the fast path,
   inherited from the base schema editor), or
2. Rebuilding the whole table by creating a new table with the desired
   definition and copying the data across (the "remake table" path).

SQLite's `ALTER TABLE ... ADD COLUMN` cannot add a column that is a primary
key or that carries a `UNIQUE` constraint, and it cannot add a column whose
definition requires dropping a default afterwards. When a caller adds a
nullable one-to-one field (which is unique but nullable), the old logic chose
the plain `ALTER TABLE ADD COLUMN` path because the field permits NULL and has
no effective default. SQLite then rejects the statement with
`OperationalError: Cannot add a UNIQUE column`, crashing the migration.

The goal is to make `add_field` recognize that primary-key and unique fields
must be added via the table-remake path on SQLite, so that adding a nullable
one-to-one (or otherwise unique) field succeeds and produces a correctly
defined column, while all previously working cases continue to behave exactly
as before.

## Requirement 1: Adding a unique or one-to-one field uses the table-remake path

**User story:** As a developer running a migration that adds a nullable
one-to-one field on SQLite, I want the field to be created without a database
error, so that my migrations apply successfully on SQLite as they do on other
backends.

**Acceptance criteria**
1. WHEN `add_field` is asked to add a field whose definition carries a UNIQUE
   constraint (including a one-to-one field), THEN the SQLite schema editor
   SHALL create the field by remaking the table rather than by issuing a plain
   `ALTER TABLE ... ADD COLUMN` statement.
2. WHEN `add_field` is asked to add a nullable one-to-one field to an existing
   populated or empty model, THEN the operation SHALL complete without raising
   a database error (in particular, without SQLite's "Cannot add a UNIQUE
   column" error).
3. WHEN a nullable one-to-one field has been added, THEN the resulting table
   SHALL contain the new column and that column SHALL permit NULL values.
4. WHEN `add_field` is asked to add a field that is a primary key, THEN the
   SQLite schema editor SHALL create the field by remaking the table rather
   than by issuing a plain `ALTER TABLE ... ADD COLUMN` statement.

## Requirement 2: Preserve existing add-field behavior for other field kinds

**User story:** As a maintainer of the SQLite backend, I want the existing
add-field decisions to stay unchanged for all other field kinds, so that this
change fixes the unique-column case without regressing established behavior.

**Acceptance criteria**
1. WHEN `add_field` is asked to add a non-nullable field, THEN the schema
   editor SHALL continue to create the field by remaking the table.
2. WHEN `add_field` is asked to add a field that has an effective (non-null)
   default value, THEN the schema editor SHALL continue to create the field by
   remaking the table.
3. WHEN `add_field` is asked to add a field that is nullable, has no effective
   default, is not a primary key, and carries no UNIQUE constraint, THEN the
   schema editor SHALL continue to create the field using the inherited plain
   `ALTER TABLE ... ADD COLUMN` behavior.
4. The system SHALL keep producing column definitions, defaults, and
   nullability for all previously supported add-field cases identical to their
   prior behavior, so that adding ordinary nullable and non-nullable columns,
   binary fields, defaulted fields, and text/data-transformed fields continues
   to work as before.
5. WHEN a field is added via the table-remake path, THEN the schema editor
   SHALL preserve the existing rows and other columns of the table unchanged.
