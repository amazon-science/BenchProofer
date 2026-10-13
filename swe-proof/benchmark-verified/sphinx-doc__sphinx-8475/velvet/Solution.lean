import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The behaviour this slice depends on — how a failed link
   probe is CLASSIFIED, and which failures the lightweight first attempt retries
   with a full fetch — is modeled DEEPLY in the `pure` region (`classifyReached`,
   `classifyUnhandled`, and the inline retry predicate) over an abstract failure
   carrier, and validated == the real failure hierarchy by G-AX (an A-reference,
   mapping.md §3). It carries no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- A failed probe of a remote target, in the three shapes the desired behaviour
   distinguishes:
     * `statusError code` — the server answered with an error status `code`
       (the only observed field is the status number);
     * `redirectLoop` — the target kept redirecting until the redirect budget
       was exhausted, so no response was obtained;
     * `otherFailure` — any other failure (connection, TLS, decoding, …).
   The behaviour distinguishes only these three, because only these three are
   routed differently by the classification below. -/
inductive RequestFailure where
  | statusError (code : Nat)
  | redirectLoop
  | otherFailure
  deriving DecidableEq

/- The outcome of one attempt to probe a target:
     * `reached sameTarget` — a response was obtained and accepted; `sameTarget`
       records whether the final location equals the requested one (`true`) or
       the request was sent onward to a different location (`false`);
     * `failed e` — the attempt failed in one of the ways above. -/
inductive Probe where
  | reached (sameTarget : Bool)
  | failed (e : RequestFailure)
  deriving DecidableEq

/- The status a link is reported with. -/
inductive LinkStatus where
  | working
  | ignored
  | broken
  | redirected
  deriving DecidableEq

/- Classification of a successfully reached target: a target whose final
   location is the requested one is `working`; one that was sent onward to a
   different final location is `redirected`. -/
def classifyReached (sameTarget : Bool) : LinkStatus :=
  if sameTarget then .working else .redirected

/- Classification of a failure that was NOT retried (it reached the top-level
   handler): a status-carrying failure is read by its code — an authorization
   challenge (401) is still treated as `working`, a temporary-unavailable
   response (503) is `ignored`, any other status is a failed link; a
   redirect-budget exhaustion and every other failure are also failed links. -/
def classifyUnhandled (e : RequestFailure) : LinkStatus :=
  match e with
  | .statusError 401 => .working
  | .statusError 503 => .ignored
  | .statusError _   => .broken
  | .redirectLoop    => .broken
  | .otherFailure    => .broken

/- A failure should be retried with a full fetch when it is a status-carrying
   failure OR a redirect-budget exhaustion — both are scenarios where a server
   that mishandles the lightweight first attempt may still serve a full fetch.
   Any other failure is not retried. -/
def retriable (e : RequestFailure) : Bool :=
  match e with
  | .statusError _ => true
  | .redirectLoop  => true
  | .otherFailure  => false

/- The reported status of a link, as a function of the lightweight first probe
   (`headProbe`) and, when the first probe's failure is retriable, a full-fetch
   second probe (`getProbe`):
     * if the first probe reached the target, classify it;
     * if it failed retriably, perform the second probe and classify ITS outcome
       (a second-probe failure reaches the top-level handler);
     * if it failed non-retriably, that failure reaches the top-level handler. -/
def resolveLinkStatusSpec (headProbe getProbe : Probe) : LinkStatus :=
  match headProbe with
  | .reached sameTarget => classifyReached sameTarget
  | .failed e =>
      if retriable e then
        match getProbe with
        | .reached sameTarget => classifyReached sameTarget
        | .failed e2          => classifyUnhandled e2
      else
        classifyUnhandled e

@[grind] lemma resolveLinkStatusSpec_reached (b : Bool) (g : Probe) :
    resolveLinkStatusSpec (.reached b) g = classifyReached b := rfl
@[grind] lemma resolveLinkStatusSpec_failed (e : RequestFailure) (g : Probe) :
    resolveLinkStatusSpec (.failed e) g =
      (if retriable e then
        (match g with
         | .reached b => classifyReached b
         | .failed e2 => classifyUnhandled e2)
      else classifyUnhandled e) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method resolveLinkStatus (headProbe : Probe) (getProbe : Probe) return (out : LinkStatus)
  ensures out = resolveLinkStatusSpec headProbe getProbe
  do
    -- impl-start
    let out : LinkStatus :=
      match headProbe with
      | .reached sameTarget => classifyReached sameTarget
      | .failed e =>
          -- The first probe failed: decide whether to retry with a full fetch.
          -- A status-carrying failure OR a redirect-budget exhaustion is
          -- retried; any other failure is not.
          if retriable e then
            match getProbe with
            | .reached sameTarget => classifyReached sameTarget
            | .failed e2          => classifyUnhandled e2
          else
            classifyUnhandled e
    return out
    -- impl-end

prove_correct resolveLinkStatus by
  loom_solve
