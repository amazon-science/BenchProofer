# Requirements: Add a `--skip-checks` option to the `runserver` command

## Introduction

Django's development web server is started by the `runserver` management command
(`django/core/management/commands/runserver.py`). Before it begins serving, its
startup routine (`Command.inner_run`) announces that it is performing system
checks, runs the framework's system checks, runs the migration check, prints the
startup banner, and then starts serving requests.

At the base revision the system-check step (the "Performing system checks..."
announcement plus the call that runs the system checks) is performed
unconditionally on every startup — and, because `runserver` uses the
auto-reloader, on every reload. Other management commands already accept a
`--skip-checks` option to bypass these checks; `runserver` does not. During
active development this makes every reload wait on system checks even when the
developer would rather run checks only in CI/CD.

The goal is to add a `--skip-checks` option to the `runserver` command
(registered in `Command.add_arguments`) that, when enabled, causes the startup
routine to omit the system-check step, while leaving every other startup
behavior — the migration check, the banner, and serving — unchanged.

## Requirement 1: Register a `--skip-checks` option for `runserver`

**User story:** As a developer running the development server, I want a
`--skip-checks` option on `runserver`, so that I can start the server without
paying for system checks on every (re)start, consistent with other management
commands.

**Acceptance criteria**

1. The `runserver` command SHALL accept a `--skip-checks` command-line option.
2. WHEN the `runserver` command is invoked without `--skip-checks`, THEN the
   command SHALL treat the skip-checks control as disabled (its default is a
   disabled/false state).
3. WHEN `--skip-checks` is supplied on the command line, THEN the command SHALL
   treat the skip-checks control as enabled.
4. The `--skip-checks` option SHALL be a boolean flag that takes no value and
   SHALL be documented in the command's help text as skipping system checks.

## Requirement 2: Skip the system-check step when skip-checks is enabled

**User story:** As a developer, I want the server to skip system checks when I
ask it to, so that startup and reloads are faster during development.

**Acceptance criteria**

1. IF the skip-checks control is enabled when the startup routine
   (`Command.inner_run`) runs, THEN the routine SHALL NOT write the "Performing
   system checks..." announcement to standard output.
2. IF the skip-checks control is enabled, THEN the startup routine SHALL NOT
   invoke the system-check operation (`Command.check`).
3. WHEN skip-checks is enabled, THEN the omission of the system-check step SHALL
   be the only change to the startup routine's behavior relative to skip-checks
   being disabled.

## Requirement 3: Perform the system-check step when skip-checks is disabled

**User story:** As a developer who has not opted out, I want the server to keep
performing system checks at startup, so that existing behavior is preserved by
default.

**Acceptance criteria**

1. WHEN the startup routine runs with the skip-checks control disabled, THEN the
   routine SHALL write the "Performing system checks..." announcement to standard
   output.
2. WHEN the startup routine runs with the skip-checks control disabled, THEN the
   routine SHALL invoke the system-check operation (`Command.check`) with error
   counts displayed, exactly as before this option existed.
3. The system-check announcement and the system-check call SHALL either both be
   performed (skip-checks disabled) or both be omitted (skip-checks enabled);
   the announcement SHALL NOT appear without the corresponding check call, nor
   vice versa.

## Requirement 4: Preserve all other startup behavior regardless of skip-checks

**User story:** As a maintainer, I want adding `--skip-checks` to leave every
other aspect of `runserver` unchanged, so that the new option does not regress
existing behavior.

**Acceptance criteria**

1. The startup routine SHALL run the migration check (`Command.check_migrations`)
   on every startup, regardless of whether skip-checks is enabled or disabled.
2. The startup routine SHALL write the startup banner (Django version, settings
   module, and the server address/port) and begin serving on every startup,
   regardless of the skip-checks control.
3. The system SHALL continue to support the `runserver` command's existing
   options and behaviors — including address/port parsing, the IPv6 option, the
   no-threading option, and the no-reload option — unchanged by the addition of
   `--skip-checks`.
4. WHEN the auto-reloader is disabled for a run, THEN the startup routine SHALL
   still honor the skip-checks control exactly as specified in Requirements 2
   and 3.
