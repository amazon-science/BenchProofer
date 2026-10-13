# Requirements: Expose a command-line option to skip a management command's system checks

## Introduction

Django management commands run a battery of project "system checks" before they
do their work, controlled by the per-command `requires_system_checks` attribute.
An internal, undocumented way to bypass those checks already existed (a
`skip_checks` value that could be threaded through the programmatic
`call_command` entry point), but there was no way to request it from the command
line. This change exposes that capability as a first-class command-line option,
`--skip-checks`, on `BaseCommand` (`django/core/management/base.py`), so that a
user invoking a command through `manage.py` / `django-admin` can move ahead with
the task at hand without first fixing an unrelated system-check failure.

The affected surface is:

- `BaseCommand.create_parser()` — where the shared, common options are added to
  the argument parser.
- `BaseCommand.execute()` — where the decision to run system checks is made.
- `BaseCommand.base_stealth_options` — the set of option names accepted by
  `call_command` that are not defined on the argument parser.
- `DjangoHelpFormatter` — which groups common options after command-specific
  ones in `--help` output.

The goal: a command that performs system checks gains an opt-in `--skip-checks`
flag; supplying it suppresses the checks for that invocation, while the default
(flag absent) preserves today's behavior of running the checks.

## Requirement 1: Command-line flag to skip system checks

**User story:** As a developer running a management command from the command
line, I want to pass a `--skip-checks` flag, so that the command proceeds
without running project system checks when I choose to bypass them.

**Acceptance criteria**

1. The system SHALL make a boolean command-line option named `--skip-checks`
   available on every management command whose `requires_system_checks`
   attribute is true.
2. The `--skip-checks` option SHALL be a store-true flag that takes no value and
   defaults to a "not requested" (false) state when it is not supplied.
3. WHEN a command whose `requires_system_checks` is true is invoked from the
   command line with `--skip-checks`, THEN the command SHALL NOT run its system
   checks, and SHALL proceed to execute its normal handling and produce its
   normal output.
4. WHEN a command whose `requires_system_checks` is true is invoked with
   `--skip-checks` and the project would otherwise fail a system check, THEN the
   command SHALL still execute normally and SHALL NOT emit that check's error or
   warning output.
5. WHEN a command whose `requires_system_checks` is true is invoked WITHOUT
   `--skip-checks`, THEN the command SHALL run its system checks before invoking
   its handler.

## Requirement 2: The flag is offered only by commands that perform checks

**User story:** As a maintainer, I want the skip option to appear only where it
is meaningful, so that commands which never run system checks do not advertise a
useless flag.

**Acceptance criteria**

1. IF a command's `requires_system_checks` attribute is false, THEN the system
   SHALL NOT add the `--skip-checks` option to that command's argument parser.
2. IF a command's `requires_system_checks` attribute is false, THEN that command
   SHALL proceed without running system checks regardless of any skip request.
3. WHEN evaluating whether to run system checks in `execute()`, THEN the system
   SHALL treat a command that requires checks and was not asked to skip them as
   the only case in which the checks run; in all other cases the checks SHALL be
   omitted.

## Requirement 3: Programmatic skip behavior is preserved

**User story:** As a developer calling commands programmatically, I want the
existing ability to skip checks through the internal call path to keep working,
so that this change does not regress `call_command`.

**Acceptance criteria**

1. The system SHALL continue to accept a `skip_checks` keyword when a command is
   invoked programmatically through `call_command`, without treating it as an
   unrecognized option.
2. WHEN a command that requires system checks is invoked programmatically with a
   truthy `skip_checks`, THEN the system checks SHALL NOT run.
3. The system SHALL continue to reject genuinely unknown options passed through
   `call_command` by raising an error, so that removing `skip_checks` from the
   internal stealth-option set does not weaken that validation.
4. The `stderr` and `stdout` stream overrides SHALL remain accepted as
   non-parser options passed through `call_command`.

## Requirement 4: Help output grouping and existing common options preserved

**User story:** As a user reading a command's `--help`, I want the common
options (including the new skip flag) to remain grouped together after the
command-specific arguments, so that help output stays consistent.

**Acceptance criteria**

1. The system SHALL present `--skip-checks` among the common options that
   `DjangoHelpFormatter` orders after a command's command-specific arguments.
2. The system SHALL keep offering all previously available common options
   (`--version`, `--verbosity`, `--settings`, `--pythonpath`, `--traceback`,
   `--no-color`, `--force-color`) and SHALL keep ordering them after
   command-specific arguments.
3. The system SHALL keep passing through any keyword arguments given to
   `create_parser()` when constructing the command's argument parser.
4. WHEN `--skip-checks` is provided, THEN it SHALL describe itself in help text
   as skipping system checks.
