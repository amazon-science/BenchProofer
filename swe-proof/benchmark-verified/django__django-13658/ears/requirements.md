# Requirements: Program name in django-admin / manage.py utility must derive from the passed argument vector

## Introduction

Django's command-line entry point (`django.core.management.execute_from_command_line`,
implemented by `django.core.management.ManagementUtility`) is invoked with an
argument vector (`argv`). When no vector is supplied it falls back to the
process-global `sys.argv`. `ManagementUtility.__init__` already computes a
program name (`self.prog_name`) from *its own* argument vector: the final path
component of `argv[0]`, with the special case that a final component of
`__main__.py` is presented as `python -m django`.

However, when `ManagementUtility.execute()` builds the internal
`CommandParser` (from `django.core.management.base`) used to preprocess the
`--settings` and `--pythonpath` options, it constructs that parser without
telling it the program name. Because `CommandParser` derives from
`argparse.ArgumentParser`, the `%(prog)s` placeholder in the parser's `usage`
string then falls back to the process-global `sys.argv[0]` rather than the
already-computed `self.prog_name`. As a result, usage/help banners emitted
through that parser (and any error banner it produces) show the wrong program
name whenever the caller's `argv[0]` differs from `sys.argv[0]` — including the
embedded-use case where `sys.argv[0]` is missing or `None`.

The goal: the program name presented by the utility must be a function of the
argument vector the utility was given, independent of the ambient process
argument vector, while preserving all existing command-line behavior.

## Requirement 1: Program name is derived from the utility's own argument vector

**User story:** As a developer embedding Django's management entry point, I want
`execute_from_command_line(argv)` to compute the presented program name from the
`argv` I pass, so that the utility works correctly even when the ambient
`sys.argv[0]` is incorrect, missing, or `None`.

**Acceptance criteria**

1. WHEN `execute_from_command_line` is called with an explicit argument vector,
   THEN the utility SHALL compute the presented program name from the first
   element of that supplied vector and SHALL NOT read the ambient process
   argument vector to determine it.
2. WHEN the utility produces the usage/help banner of the option parser it uses
   to preprocess options, THEN the program name shown in that banner SHALL be
   the program name computed from the supplied argument vector.
3. IF the supplied argument vector's first element differs from the ambient
   process argument vector's first element, THEN the presented program name
   SHALL reflect the supplied vector's first element and SHALL NOT reflect the
   ambient one.
4. The system SHALL compute the presented program name as the final
   path component (the portion after the last `/` separator) of the supplied
   argument vector's first element.
5. IF that final path component equals `__main__.py`, THEN the presented program
   name SHALL be the constant string `python -m django`.
6. WHEN two invocations are made with equal utility argument vectors but
   differing ambient process argument vectors, THEN both invocations SHALL
   present the same program name.

## Requirement 2: Requesting help for a subcommand shows the correct program name and no error output

**User story:** As a user running the utility with an explicit argument vector,
I want a subcommand's help output to be titled with the program name I invoked,
so that the usage instructions are accurate.

**Acceptance criteria**

1. WHEN the utility is asked to display help for a specific subcommand, THEN the
   emitted usage line SHALL begin with the presented program name (derived from
   the supplied argument vector) followed by the subcommand name.
2. WHEN help for a subcommand is displayed under normal (non-error) conditions,
   THEN the utility SHALL write the help text to standard output and SHALL write
   nothing to standard error.
3. WHEN the supplied argument vector's first element and the ambient process
   argument vector's first element differ, THEN the subcommand help usage line
   SHALL still show the program name from the supplied argument vector.

## Requirement 3: Preserve existing command-line behavior (regression protection)

**User story:** As a maintainer, I want the existing behavior of `django-admin`,
`manage.py`, and `python -m django` to remain unchanged, so that only the
program-name source is corrected and no other functionality regresses.

**Acceptance criteria**

1. The system SHALL continue to preprocess the `--settings` and `--pythonpath`
   options early, before command resolution, applying their effects as before.
2. WHEN invalid or unrecognized options are encountered during that early
   preprocessing, THEN the utility SHALL ignore those option errors at that
   stage rather than aborting, exactly as before.
3. WHEN the utility is invoked with no explicit argument vector, THEN it SHALL
   fall back to the ambient process argument vector to determine its argument
   vector and its program name.
4. The system SHALL continue to present `python -m django` as the program name
   when invoked as the module-execution entry point, in help and version output
   as before.
5. The system SHALL continue to support the special cases `--help`, `-h`,
   `--version`, the `help` subcommand (including `help --commands`), and the
   `version` subcommand with their existing output and behavior.
6. WHEN a subcommand is executed, THEN the utility SHALL continue to dispatch it
   using the supplied argument vector, preserving existing runserver, startapp,
   startproject, check, diffsettings, and user-command behavior.
7. The system SHALL continue to emit "Unknown command" messages and command
   suggestions using the presented program name for the "Type '<prog> help' for
   usage." hint.
