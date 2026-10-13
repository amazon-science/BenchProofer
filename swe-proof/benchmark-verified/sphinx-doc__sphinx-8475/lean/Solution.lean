import Mathlib
-- imports-end

/-!
Probing a URL with a lightweight request and a full-request fallback.

To check whether a link works, a lightweight probe is attempted first (it is
easier on the server and the network than downloading the whole resource). That
probe can finish in one of several ways:

  * it succeeds and yields a usable response;
  * it fails with an HTTP status error (the server answered, but with an error
    status);
  * it fails because the server keeps redirecting without ever settling — a
    redirect loop;
  * it fails for some other reason (the connection could not be established, the
    certificate was rejected, and so on).

When the lightweight probe fails with a *retryable* condition — an HTTP status
error, OR a redirect loop (some servers only loop on the lightweight probe and
answer a full request fine) — the check falls back to a full request and reports
that request's outcome instead. Any other failure is reported as-is; a successful
probe is reported as-is.

We model the surviving outcome as `ReqOutcome`. The result is fully determined by
the two probe outcomes (the lightweight one and the fallback one): it is the
fallback outcome exactly when the lightweight outcome is a retryable failure, and
the lightweight outcome otherwise.
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom: the two request outcomes are the
-- modeled function's INPUTS (the network results), and the retry decision is
-- modeled deeply in the `pure` region. Hence no `opaque`/`axiom` declarations.
-- axioms-end

-- pure-start
/-- The possible outcomes of a single network probe. `ok` is a usable response;
the others are the distinct failure modes that the decision below treats
differently. -/
inductive ReqOutcome where
  | ok             -- a usable response was obtained
  | statusError    -- the server answered with an error status
  | redirectLoop   -- the server kept redirecting without settling
  | otherFailure   -- any other failure (connection, certificate, …)
deriving DecidableEq, Repr, Inhabited

/-- Whether a failed lightweight probe should be retried with a full request.
A retry is warranted for an HTTP status error and for a redirect loop; every
other outcome (including success) is not retried. -/
def retryWithFull : ReqOutcome → Bool
  | ReqOutcome.statusError  => true
  | ReqOutcome.redirectLoop => true
  | _                       => false
-- pure-end

-- post-conditions-start
/-- The surviving outcome of probing a URL. `light` is the lightweight probe's
outcome and `full` is the fallback full-request outcome. The result is the
fallback outcome exactly when the lightweight outcome is a retryable failure, and
the lightweight outcome itself otherwise. -/
def problem_spec_probeUri
    (light full : ReqOutcome) (result : ReqOutcome) : Prop :=
  result = if retryWithFull light then full else light
-- post-conditions-end

-- impl-start
def implementation_probeUri (light full : ReqOutcome) : ReqOutcome :=
  Id.run do
    let mut response := light
    if retryWithFull light then
      response := full
    return response
-- impl-end

-- proof-start
theorem correct_probeUri :
    ∀ (light full : ReqOutcome),
      problem_spec_probeUri light full (implementation_probeUri light full) := by
  intro light full
  unfold problem_spec_probeUri implementation_probeUri
  by_cases h : retryWithFull light <;> simp only [Id.run, h, if_true] <;> rfl
-- proof-end
