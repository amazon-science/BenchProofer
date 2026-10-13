# Requirements: Simplify the flush-execution routine to infer its target database

## Introduction

Django's database backends expose a helper that runs a list of SQL statements
which clear ("flush") a database, wrapping them in a single transaction. This
helper lives on the base database-operations class
(`django.db.backends.base.operations.BaseDatabaseOperations`) and is named
`execute_sql_flush`. Historically it accepted an explicit target-database
identifier as its first positional argument, even though every caller passed the
alias of the very connection the operations object already belongs to. That
identifier is therefore redundant: the operations object already knows which
database it talks to, via `self.connection.alias`.

The goal is to simplify the helper's signature so the redundant identifier is no
longer accepted, and to have the routine derive the target database from the
connection itself. All existing callers (including the `flush` management
command in `django.core.management.commands.flush`) must be updated to the new
signature, and the runtime behavior of clearing the database — one transaction,
correct savepoint behavior, every statement executed in order — must be
preserved exactly.

## Requirement 1: Infer the target database from the connection

**User story:** As a developer calling the SQL-flush execution helper, I want it
to determine the target database automatically from the connection it belongs
to, so that I do not have to pass a redundant database identifier that is always
the connection's own alias.

**Acceptance criteria**

1. The system SHALL provide `BaseDatabaseOperations.execute_sql_flush` accepting
   a single caller-supplied positional argument: the list of SQL statements to
   run. It SHALL NOT require or accept a separate target-database identifier
   argument.
2. WHEN `execute_sql_flush` is invoked, THEN the helper SHALL open its
   transaction against the database named by its own connection's alias
   (`self.connection.alias`), not against any externally provided identifier.
3. WHEN `execute_sql_flush` is invoked with the list of SQL statements as its
   only positional argument, THEN it SHALL execute successfully and clear the
   database without raising a `TypeError` for a missing or unexpected argument.
4. IF a caller invokes `execute_sql_flush` using the previous two-argument form
   (a database identifier followed by the statement list), THEN the call SHALL
   fail rather than silently treating the extra value as valid input.

## Requirement 2: Preserve transactional flush behavior

**User story:** As a database backend maintainer, I want the flush execution to
keep its exact transactional and ordering semantics after the signature change,
so that database clearing remains correct and safe.

**Acceptance criteria**

1. WHEN `execute_sql_flush` runs, THEN the supplied SQL statements SHALL all be
   executed within a single transaction bound to the connection's own database
   alias.
2. WHEN the transaction is opened, THEN its savepoint behavior SHALL be
   determined by the backend's rollback-capability flag
   (`self.connection.features.can_rollback_ddl`).
3. WHEN `execute_sql_flush` runs, THEN it SHALL execute each supplied SQL
   statement exactly once, through a cursor on the connection, in the same order
   the statements were provided.
4. WHEN `execute_sql_flush` completes after running the flush statements against
   populated tables, THEN the affected tables SHALL contain no rows.

## Requirement 3: Update all internal callers to the new signature

**User story:** As a Django user running database management commands, I want the
`flush` command and other internal users of the helper to keep working after the
signature simplification, so that flushing a database continues to succeed.

**Acceptance criteria**

1. WHEN the `flush` management command clears the selected database, THEN it
   SHALL call `execute_sql_flush` with only the SQL statement list, and SHALL NOT
   pass a separate database identifier.
2. The system SHALL continue to honor the command's `--database` option when
   selecting which connection to flush, so that the correct database's tables are
   cleared.
3. IF executing the flush statements raises an exception, THEN the `flush`
   command SHALL surface a command-level error explaining that the database could
   not be flushed, preserving its existing error-reporting behavior.
4. The system SHALL keep every other internal caller of `execute_sql_flush`
   consistent with the single-argument signature, so that no caller passes a
   redundant database identifier.
