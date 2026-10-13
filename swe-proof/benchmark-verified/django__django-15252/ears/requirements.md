# Requirements: MigrationExecutor must not create the migration-bookkeeping table when there is nothing to record

## Introduction

Django records which migrations have been applied in a small bookkeeping table
(`django_migrations`), managed by `MigrationRecorder`
(`django/db/migrations/recorder.py`). Before running a batch of migration
operations, `MigrationExecutor.migrate()`
(`django/db/migrations/executor.py`) unconditionally invoked the recorder's
schema-provisioning step, which creates that table (issuing a `CREATE TABLE`
via the schema editor) whenever it is absent.

This is wrong when there is no migration work to record. In multi-database
setups — for example when a database router forbids migrating a connection, or
when a test database is configured with `TEST['MIGRATE'] = False` — Django
would still create the `django_migrations` table on connections that should
never receive it. The provisioning step should only happen when there are
migrations to apply/record.

The goal is to make `MigrationExecutor.migrate()` skip table provisioning when
the caller explicitly passes an empty plan, while leaving all other behavior
(including normal migration application and recording) unchanged. The affected
function is the head of `MigrationExecutor.migrate()`, which consults the
recorder's `has_table()` and `ensure_schema()` helpers (`recorder.py`) and may
return an early project state built by the executor's `_create_project_state`
helper.

## Requirement 1: Do not provision the bookkeeping table for an explicitly empty plan

**User story:** As a developer with a multi-database (routed) setup, I want the
migration executor to avoid creating the `django_migrations` bookkeeping table
on connections where there are no migrations to apply, so that read-only or
non-default connections are left untouched.

**Acceptance criteria**

1. WHEN `MigrationExecutor.migrate()` is called with `plan` explicitly set to an
   empty list (`plan == []`), THEN the executor SHALL NOT invoke the recorder's
   schema-provisioning step (`ensure_schema()`) — it SHALL NOT attempt to create
   or provision the `django_migrations` table.
2. IF `MigrationExecutor.migrate()` is called with an explicitly empty plan AND
   the bookkeeping table does not exist (the recorder's `has_table()` reports
   `False`), THEN the executor SHALL return immediately with a project state
   built with no applied migrations (the state produced by its
   `_create_project_state` helper for the no-applied-migrations case), without
   executing the remainder of the migration procedure.
3. WHILE handling an explicitly empty plan whose bookkeeping table is absent,
   the executor SHALL issue no database queries — in particular it SHALL perform
   no schema-editor / `CREATE TABLE` operation.
4. IF `MigrationExecutor.migrate()` is called with an explicitly empty plan AND
   the bookkeeping table already exists (the recorder's `has_table()` reports
   `True`), THEN the executor SHALL NOT provision the table and SHALL proceed
   through the remaining migration steps to produce and return the resulting
   project state.

## Requirement 2: Continue provisioning the table when there is work to record

**User story:** As a developer applying migrations, I want the executor to keep
ensuring the bookkeeping table exists whenever migrations may actually be
applied, so that applied migrations can still be recorded correctly.

**Acceptance criteria**

1. WHEN `MigrationExecutor.migrate()` is called with `plan` left unset/`None`
   (so the executor computes the plan itself), THEN the executor SHALL invoke
   the recorder's schema-provisioning step (`ensure_schema()`) before proceeding,
   exactly as before.
2. WHEN `MigrationExecutor.migrate()` is called with a non-empty `plan`, THEN the
   executor SHALL invoke the recorder's schema-provisioning step
   (`ensure_schema()`) before proceeding.
3. The distinction between an explicitly empty plan and an unset plan SHALL be
   preserved: passing `plan == []` SHALL be treated as "nothing to do" (per
   Requirement 1), whereas passing no plan (`None`) SHALL trigger provisioning
   as in criterion 1 of this requirement.

## Requirement 3: Preserve existing migration behavior (regression protection)

**User story:** As a Django maintainer, I want all existing migration
application, rollback, and recording behavior to remain intact, so that this
change fixes only the unnecessary table creation and nothing else.

**Acceptance criteria**

1. WHEN `MigrationExecutor.migrate()` runs for a non-empty forwards or backwards
   plan, THEN it SHALL apply the planned migrations and record/unrecord them, and
   SHALL return the correct resulting project state, exactly as before this
   change.
2. WHEN `MigrationExecutor.migrate()` is called with an unset plan and the target
   state already matches the current state, THEN it SHALL make no unnecessary
   changes and SHALL return the appropriate project state, as before.
3. The system SHALL continue to reject mixed forwards-and-backwards plans and to
   run replacement/squash bookkeeping (`check_replacements`) as it did before.
4. The `MigrationRecorder` helpers SHALL retain their existing semantics: the
   system SHALL report the table's presence via `has_table()`, SHALL create the
   table on demand via `ensure_schema()` when it is absent, and SHALL still
   record and unrecord individual migrations when those operations are invoked.
5. WHEN a test database is created with its `TEST['MIGRATE']` setting disabled
   (so migration application is skipped and `migrate` is reached with an empty
   plan), THEN the creation routine SHALL NOT provision the bookkeeping table,
   AND SHALL still synchronize the unmigrated applications for that database.
6. WHEN a test database is created with its `TEST['MIGRATE']` setting enabled,
   THEN the creation routine SHALL proceed to apply migrations as before this
   change.
