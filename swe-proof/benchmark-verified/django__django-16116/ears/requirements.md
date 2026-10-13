# Requirements: `makemigrations --check` must not write migrations

## Introduction

The `makemigrations` management command (`django/core/management/commands/makemigrations.py`,
`Command.handle`) supports a `--check` flag (stored as the `check_changes`
option) whose purpose is to let a script detect whether model changes are
missing their migrations. Historically, when `--check` was supplied and model
changes were detected, the command wrote the new migration files to disk and
*then* exited with a non-zero status. This is inconsistent with the `--check`
behavior of other management commands (for example `migrate --check` and
`optimizemigration --check`), which report the condition and exit without
performing the underlying write/apply action.

The goal is to make `makemigrations --check` behave consistently: when changes
are detected it must exit with a non-zero status **without** creating any
migration files, so that a caller no longer has to combine `--check` with
`--dry-run` to avoid side effects. The normal (non-`--check`) code paths that
write migration files, and all other command behaviors, must be preserved.

## Requirement 1: `--check` exits early without writing migrations when changes exist

**User story:** As a developer scripting a CI check, I want `makemigrations
--check` to tell me that migrations are missing and exit non-zero without
creating any migration files, so that I can detect the condition without
mutating my working tree.

**Acceptance criteria**

1. WHEN `Command.handle` is invoked with the `check_changes` option enabled and
   the change-detection step reports one or more apps requiring new migrations,
   THEN the command SHALL terminate the process immediately with a non-zero exit
   status.
2. WHEN `Command.handle` terminates early due to `check_changes` with detected
   changes, THEN the command SHALL NOT write any new migration file to the
   migrations directory.
3. WHEN `Command.handle` terminates early due to `check_changes` with detected
   changes, THEN the command SHALL NOT merge or rewrite any existing (latest)
   migration file.
4. IF `check_changes` is enabled and changes are detected, THEN the early
   termination SHALL occur before any migration-writing step (whether the
   fresh-file writer or the update-last-migration writer) is reached, so that no
   filesystem output is produced as a side effect of the check.

## Requirement 2: Writing migrations still happens when `--check` is not requested

**User story:** As a developer running `makemigrations` normally, I want
migration files to continue to be generated when changes are detected, so that
the command's primary function is unaffected by the `--check` change.

**Acceptance criteria**

1. WHEN changes are detected and `check_changes` is not enabled and update mode
   is not enabled, THEN the command SHALL write the detected changes as new
   migration files.
2. WHEN changes are detected and `check_changes` is not enabled and update mode
   is enabled, THEN the command SHALL write the detected changes into the latest
   existing migration files instead of creating fresh ones.
3. WHEN changes are detected and `check_changes` is not enabled, THEN the
   command SHALL complete normally (SHALL NOT request a non-zero early exit for
   the reason of missing migrations).

## Requirement 3: No changes detected behaves as before

**User story:** As a developer, I want `makemigrations` (with or without
`--check`) to do nothing and complete successfully when there are no model
changes, so that a clean project passes the check.

**Acceptance criteria**

1. WHEN the change-detection step reports no apps requiring new migrations, THEN
   the command SHALL NOT write or modify any migration file.
2. WHEN no changes are detected, THEN the command SHALL complete normally
   without requesting a non-zero early exit, regardless of whether
   `check_changes` is enabled.
3. WHILE no changes are detected and verbosity permits informational output, the
   command SHALL report that no changes were detected.

## Requirement 4: `--check` help text reflects the no-write behavior

**User story:** As a user reading `makemigrations --help`, I want the `--check`
option description to state that it does not write migrations, so that the
documented behavior matches the implementation.

**Acceptance criteria**

1. The system SHALL describe the `--check` option as exiting with a non-zero
   status when model changes are missing migrations and as not writing those
   migrations.
