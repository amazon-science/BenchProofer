# Requirements: Foreign-key constraint checking must tolerate SQL-keyword identifiers on SQLite

## Introduction

When Django's SQLite backend verifies deferred foreign-key constraints, it
builds raw SQL by substituting a table name (and, for reporting a violation,
the primary-key and foreign-key column names) directly into `PRAGMA` and
`SELECT` statements. Because those identifiers are interpolated as bare text,
any identifier that collides with a SQL reserved word — for example a table
whose database name is `order`, or a primary-key or foreign-key column whose
database name is itself a reserved word — is
parsed as syntax rather than as a name, and SQLite raises an
`OperationalError` ("near \"order\": syntax error"). This surfaces to users as
a crash during operations that check constraints, such as loading fixtures.

The affected code is `DatabaseOperations`/`DatabaseWrapper.check_constraints`
in `django/db/backends/sqlite3/base.py`. The backend already exposes a
identifier-quoting helper, `connection.ops.quote_name`
(`django/db/backends/sqlite3/operations.py`), which wraps an identifier in
double quotes (and leaves an already-double-quoted identifier unchanged). The
goal is that every identifier interpolated into the constraint-checking
queries be rendered through that quoting helper, so that reserved-word
identifiers are handled correctly while all previously working behavior is
preserved.

## Requirement 1: Quote the table name when scanning for foreign-key violations

**User story:** As a developer whose model maps to a database table whose name
is a SQL reserved word, I want Django's SQLite foreign-key constraint check to
run without a syntax error, so that operations that check constraints (such as
loading fixtures) do not crash.

**Acceptance criteria**

1. WHEN `check_constraints` is invoked with an explicit collection of table
   names and the SQLite backend supports the foreign-key-check pragma, THEN the
   backend SHALL, for each table name, build the `PRAGMA foreign_key_check(...)`
   query with the table name rendered through `connection.ops.quote_name`
   rather than interpolated as a bare identifier.
2. IF a supplied table name is a SQL reserved word (for example `order`), THEN
   the constraint check SHALL execute the pragma without raising a database
   syntax error attributable to that identifier.
3. WHEN a table name is rendered for the pragma, THEN the backend SHALL wrap it
   in the backend's identifier delimiters (double quotes) exactly as
   `connection.ops.quote_name` would, applying no additional quoting if the
   name is already delimited.

## Requirement 2: Quote identifiers when reporting a detected violation

**User story:** As a developer, I want a detected foreign-key violation to be
reported correctly even when the offending table or its columns use
reserved-word names, so that I receive the intended `IntegrityError` instead of
a database syntax error.

**Acceptance criteria**

1. WHEN a foreign-key violation is detected for a table, THEN the backend SHALL
   build the `PRAGMA foreign_key_list(...)` query with the table name rendered
   through `connection.ops.quote_name`.
2. WHEN the backend fetches the offending row's primary-key value and the bad
   foreign-key value, THEN it SHALL render the primary-key column name, the
   foreign-key column name, and the table name in the `SELECT ... FROM ...
   WHERE rowid = ...` query, each through `connection.ops.quote_name`.
3. IF any of those identifiers (table, primary-key column, or foreign-key
   column) is a SQL reserved word, THEN building and executing the reporting
   queries SHALL NOT raise a database syntax error attributable to that
   identifier.
4. WHEN a genuine foreign-key violation exists for the checked table(s), THEN
   `check_constraints` SHALL raise an `IntegrityError` (not a database syntax
   error), including when the involved table and columns use reserved-word
   names.

## Requirement 3: Preserve existing constraint-checking behavior

**User story:** As a maintainer, I want the quoting change to leave all
established constraint-checking behavior intact, so that ordinary
(non-reserved-word) schemas keep working exactly as before.

**Acceptance criteria**

1. The system SHALL keep the behavior that, when `check_constraints` is called
   with no table names, all tables are checked using the plain
   `PRAGMA foreign_key_check` form without per-table interpolation.
2. WHEN `check_constraints` runs against tables with ordinary (non-reserved)
   identifiers and no violations exist, THEN it SHALL complete without raising.
3. WHEN a foreign-key violation exists under ordinary identifiers, THEN
   `check_constraints` SHALL continue to raise `IntegrityError` describing the
   offending table, primary-key value, column, bad value, and referenced
   table/column.
4. The system SHALL keep the surrounding SQL text of each query unchanged — the
   pragma names, parentheses, the column separator, and the
   `SELECT ... FROM ... WHERE rowid = ...` skeleton — altering only how the
   substituted identifiers are rendered.
5. WHEN constraint checks are disabled and then re-checked via
   `check_constraints`, THEN the disable/enable and manual constraint-check
   workflows SHALL continue to function as before for ordinary identifiers.
