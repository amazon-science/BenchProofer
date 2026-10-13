# Requirements: Preserve error formatting for management-command subparsers

## Introduction

Django management commands parse their arguments with `CommandParser`
(`django/core/management/base.py`), a subclass of `argparse.ArgumentParser`.
`CommandParser` accepts two extra construction keywords —
`missing_args_message` and `called_from_command_line` — that control how it
reports a bad or missing argument. In particular, `CommandParser.error()`
inspects `called_from_command_line`: when it is truthy the parser emits a
concise, human-facing usage/error message (the normal `argparse` behavior of
printing to stderr and exiting); when it is falsy or unset the parser raises a
`CommandError` so a programmatic caller (e.g. `call_command`) receives an
exception instead of a process exit.

A parser can create nested sub-commands via
`parser.add_subparsers().add_parser("name")`. At the affected base commit,
`CommandParser` did not override `add_subparsers()`, so the inherited
`argparse.ArgumentParser.add_subparsers()` built each sub-parser without passing
along `called_from_command_line`. Same-family sub-parsers (themselves
`CommandParser` instances) therefore defaulted the flag to `None`, losing the
parent's value. As a result, an argument error inside a sub-command surfaced as
a raw traceback on the command line instead of the same tidy usage message a
top-level argument error produces.

The goal is to make `CommandParser` propagate its error-formatting configuration
to the sub-parsers it constructs, so error reporting behaves consistently at
every nesting level, while leaving foreign parser classes untouched and
preserving all existing sub-parser behavior.

## Requirement 1: Propagate error-formatting configuration to same-family sub-parsers

**User story:** As a developer running a management command that defines
sub-commands, I want a missing or invalid argument inside a sub-command to be
reported the same way as a top-level argument error, so that I get a clear usage
message instead of a stack trace.

**Acceptance criteria**

1. `CommandParser` SHALL define its own `add_subparsers()` method that governs
   how the sub-parser factory is configured, rather than relying solely on the
   inherited `argparse.ArgumentParser.add_subparsers()`.
2. WHEN `add_subparsers()` is called on a `CommandParser` and the effective
   sub-parser class is `CommandParser` (or a subclass of it), THEN each
   sub-parser subsequently constructed via the returned sub-parsers action's
   `add_parser(...)` SHALL be created with a `called_from_command_line` value
   equal to the parent parser's own `called_from_command_line`.
3. WHEN a sub-parser has been constructed from a `CommandParser` whose
   `called_from_command_line` is truthy, and a required or otherwise invalid
   argument is encountered while parsing that sub-command, THEN the sub-parser
   SHALL report the failure as a concise usage/error message on the error output
   stream (the standard `argparse` error behavior) rather than propagating an
   unhandled traceback.
4. WHEN a sub-parser has been constructed from a `CommandParser` whose
   `called_from_command_line` is falsy or unset, and a required or otherwise
   invalid argument is encountered while parsing that sub-command, THEN the
   sub-parser SHALL raise `CommandError` (consistent with how the parent parser
   reports argument errors in that configuration).
5. The behavior in criteria 3 and 4 SHALL match the corresponding top-level
   `CommandParser` behavior for the same `called_from_command_line`
   configuration, so that sub-command argument errors and top-level argument
   errors are reported by the same mechanism.

## Requirement 2: Leave foreign parser classes unaffected

**User story:** As a developer who supplies a custom `parser_class` that is not a
`CommandParser`, I want sub-parser construction to keep working unchanged, so
that the fix does not break parsers that do not understand the extra
configuration.

**Acceptance criteria**

1. IF `add_subparsers()` is called with an effective sub-parser class that is
   NOT a subclass of `CommandParser`, THEN that parser class SHALL be used to
   construct sub-parsers without injecting a `called_from_command_line`
   argument.
2. WHEN a caller passes an explicit `parser_class` keyword to
   `add_subparsers()`, THEN that requested class SHALL determine whether the
   propagation in Requirement 1 applies (it applies only when the requested
   class is `CommandParser` or a subclass), and all other keyword arguments the
   caller passes to `add_subparsers()` SHALL still be forwarded to the
   underlying `argparse` implementation.
3. WHEN no `parser_class` keyword is supplied, THEN the parent parser's own
   class SHALL be treated as the effective sub-parser class for the purpose of
   the decision in Requirement 1.

## Requirement 3: Preserve existing sub-parser and command-parsing behavior

**User story:** As a Django user relying on existing management commands, I want
all current sub-command and argument-parsing behavior to keep working, so that
the error-formatting fix introduces no regressions.

**Acceptance criteria**

1. The system SHALL continue to support defining sub-commands via
   `parser.add_subparsers()` followed by `add_parser(...)`, and invoking such
   commands (including through `call_command`) SHALL continue to dispatch to the
   selected sub-command and honor its arguments.
2. WHEN a sub-command declares a required positional or a required sub-parser
   destination and it is supplied, THEN parsing SHALL succeed and expose the
   parsed values as before.
3. WHEN a sub-command is invoked with an unrecognized or invalid option, THEN
   the parser SHALL report the error through `CommandParser`'s normal
   argument-error path (raising `CommandError` for programmatic invocations)
   rather than crashing with an unrelated exception.
4. The system SHALL preserve the existing top-level `CommandParser` behavior for
   missing arguments, unrecognized options, mutually exclusive groups, and
   required options, so that non-sub-parser command parsing is unchanged.
5. The system SHALL preserve `BaseCommand.create_parser()` passing its keyword
   arguments through to `CommandParser`, so that parsers (and thereby their
   sub-parsers) continue to be configured with the intended error-formatting
   settings.
