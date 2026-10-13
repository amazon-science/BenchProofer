# Requirements: `call_command` support for required mutually-exclusive groups

## Introduction

Django's programmatic command runner `django.core.management.call_command`
(in `django/core/management/__init__.py`) accepts command options as keyword
arguments. Before invoking the command it simulates argument parsing by
building a parser with `command.create_parser(...)` and then, for any option
that the parser considers *required*, it re-injects that option onto the
`parse_args` list in the form `<flag>=<value>` so that argparse's own
required-argument validation is satisfied.

The defect: this re-injection only considers options whose individual argparse
action is marked `required`. An option that is **not** individually required
but belongs to a mutually-exclusive group declared with
`add_mutually_exclusive_group(required=True)` is skipped. As a result, calling
`call_command('cmd', some_dest=value)` where `some_dest` is a member of a
required mutually-exclusive group raises
`CommandError: Error: one of the arguments ... is required`, even though the
caller *did* supply one of the group's members. Passing the same value as a
string command-line token (e.g. `call_command('cmd', '--flag=value')`) works,
exposing the inconsistency.

The goal is to make keyword-argument passing recognize membership in a required
mutually-exclusive group as satisfying that group's requirement, while
preserving all existing `call_command` option-forwarding, validation, and error
behavior.

## Requirement 1: Forward keyword options that satisfy a required mutually-exclusive group

**User story:** As a developer invoking a management command programmatically,
I want to supply a member of a required mutually-exclusive group as a keyword
argument, so that the command runs without spurious "one of the arguments is
required" errors.

**Acceptance criteria**

1. WHEN `call_command` is invoked with a keyword argument whose destination
   corresponds to an option that belongs to a mutually-exclusive group declared
   as required, THEN `call_command` SHALL treat that supplied option as
   satisfying the group's requirement and SHALL forward it to argument parsing
   rather than raising a "required" error.
2. WHEN such a keyword-supplied option is forwarded to parsing, THEN
   `call_command` SHALL render it as a single string of the form
   `<flag>=<value>`, where `<flag>` is the option's shortest (lexicographically
   minimum) option string and `<value>` is the caller-supplied value.
3. WHEN a required mutually-exclusive group has multiple member options and the
   caller supplies exactly one of them as a keyword argument, THEN
   `call_command` SHALL forward only the supplied member and SHALL NOT
   fabricate or forward values for the group's other members.
4. WHEN the command executes after such a call, THEN the supplied option's
   destination SHALL be present in the options the command handler receives,
   carrying the caller-supplied value.
5. The behavior in this requirement SHALL hold regardless of which member of a
   required mutually-exclusive group the caller supplies.

## Requirement 2: Preserve required-argument-missing detection

**User story:** As a maintainer, I want the required-group validation to still
fire when nothing satisfies it, so that misuse is reported rather than silently
accepted.

**Acceptance criteria**

1. WHEN `call_command` is invoked and no member of a required mutually-exclusive
   group is supplied (neither as a keyword argument nor as a positional
   command-line token), THEN `call_command` SHALL raise `CommandError`
   reporting that one of the group's arguments is required.
2. IF a keyword argument is not individually required and does not belong to any
   required mutually-exclusive group, THEN `call_command` SHALL NOT inject it
   into the simulated parse-argument list solely on the basis of the new
   group-membership rule.

## Requirement 3: Preserve existing individually-required option forwarding

**User story:** As a maintainer, I want existing option-forwarding behavior to
keep working unchanged, so that this fix introduces no regressions.

**Acceptance criteria**

1. WHEN `call_command` receives a keyword argument whose option is individually
   marked required by the parser, THEN `call_command` SHALL continue to forward
   it to argument parsing as before.
2. The system SHALL continue to forward individually-required options whether
   they are supplied alone or mixed with positional arguments and other options.
3. The system SHALL continue to resolve caller-supplied keyword names to their
   parser destinations using the existing option-name-to-destination mapping,
   so that both the public option name and its destination name are accepted.

## Requirement 4: Preserve unknown-option and unrelated-option handling

**User story:** As a maintainer, I want validation of unknown and unrelated
options to be unaffected, so that error reporting stays correct.

**Acceptance criteria**

1. WHEN `call_command` is invoked with an option name that is neither a valid
   parser destination, a recognized stealth option, nor a mapped option name,
   THEN `call_command` SHALL raise `TypeError` identifying the unknown option(s)
   and listing the valid options.
2. The system SHALL continue to accept and correctly parse options that are not
   part of any mutually-exclusive group, including options supplied as
   command-line-style string tokens.
3. The system SHALL continue to support sub-parser (subcommand) options and
   their required-destination handling without regression.
