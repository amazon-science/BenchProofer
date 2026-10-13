import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The only callee used by the
-- modeled decision is a constant-time string equality test, which is modeled
-- DEEPLY as list equality (an I op), not axiomatized. The token values that the
-- decision compares against are taken as inputs (they are produced elsewhere and
-- are opaque to this decision). The proof agent may add `_prop` axioms only if it
-- gets stuck.
-- axioms-end

-- pure-start
/-- The decision reached when validating a stored authentication token.

* `rejected` — the token is not accepted; the principal is dropped and the
  request becomes anonymous;
* `acceptedCurrent` — the token is accepted because it equals the
  currently-valid token;
* `acceptedAlternate` — the token is accepted because it equals one of the
  additionally-accepted tokens. -/
inductive VerifyDecision
  | rejected
  | acceptedCurrent
  | acceptedAlternate
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- Validation of a stored authentication token against the currently-valid token
and a list of additionally-accepted tokens.

Inputs: `storedToken` is the token currently held in the request state (the empty
list models the absence of any token); `currentToken` is the token that is valid
under the current configuration; `alternateTokens` are additional tokens that are
also accepted.

The desired decision, by case on the stored token:

1. No stored token (`storedToken = []`): the token is rejected.
2. The stored token equals the current token: accepted against the current token.
3. The stored token differs from the current token but equals one of the accepted
   alternates: accepted against an alternate token.
4. The stored token differs from the current token and matches no alternate: the
   token is rejected.

The four cases partition the input space and each pins the decision to a single
value. -/
def problem_spec_validateToken
    (storedToken currentToken : List Char) (alternateTokens : List (List Char))
    (result : VerifyDecision) : Prop :=
  (storedToken = [] → result = .rejected) ∧
  (storedToken ≠ [] → storedToken = currentToken →
      result = .acceptedCurrent) ∧
  (storedToken ≠ [] → storedToken ≠ currentToken →
      (∃ t ∈ alternateTokens, t = storedToken) →
      result = .acceptedAlternate) ∧
  (storedToken ≠ [] → storedToken ≠ currentToken →
      (¬ ∃ t ∈ alternateTokens, t = storedToken) →
      result = .rejected)
-- post-conditions-end

-- impl-start
def implementation_validateToken
    (storedToken currentToken : List Char) (alternateTokens : List (List Char)) :
    VerifyDecision := Id.run do
  -- Pre-patch (buggy): when the stored token does not verify against the current
  -- token, the token is rejected unconditionally — the accepted alternates are
  -- never consulted.
  let mut tokenVerified := false
  if storedToken = [] then
    tokenVerified := false
  else
    tokenVerified := (storedToken == currentToken)
  if !tokenVerified then
    return .rejected
  return .acceptedCurrent
-- impl-end

-- proof-start
theorem correct_validateToken :
    ∀ (storedToken currentToken : List Char) (alternateTokens : List (List Char)),
    problem_spec_validateToken storedToken currentToken alternateTokens
      (implementation_validateToken storedToken currentToken alternateTokens) := by
  sorry   -- carries the gold proof body; UNCLOSABLE against the buggy impl (G-DIFF)
-- proof-end
