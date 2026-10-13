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
  let mut tokenVerified := false
  if storedToken = [] then
    tokenVerified := false
  else
    tokenVerified := (storedToken == currentToken)
  if !tokenVerified then
    let mut alternateMatched := false
    for t in alternateTokens do
      if t == storedToken then
        alternateMatched := true
    if storedToken != [] && alternateMatched then
      return .acceptedAlternate
    else
      return .rejected
  return .acceptedCurrent
-- impl-end


-- proof-start
theorem correct_validateToken :
    ∀ (storedToken currentToken : List Char) (alternateTokens : List (List Char)),
    problem_spec_validateToken storedToken currentToken alternateTokens
      (implementation_validateToken storedToken currentToken alternateTokens) := by
  intro st ct alts
  have loop_lemma :
      (forIn (m := Id) alts false (fun t r => if t == st then ForInStep.yield true else ForInStep.yield r))
        = (alts.any (fun t => t == st)) := by
    have gen : ∀ (b : Bool),
        (forIn (m := Id) alts b (fun t r => if t == st then pure (ForInStep.yield true) else pure (ForInStep.yield r)))
          = (b || alts.any (fun t => t == st)) := by
      intro b
      induction alts generalizing b with
      | nil => simp only [List.forIn_nil, List.any_nil, Bool.or_false]; rfl
      | cons h tl ih =>
        rw [List.forIn_cons]
        simp only [bind, pure, Id.instMonad] at *
        by_cases hh : (h == st) = true
        · simp only [hh, if_pos, ih]
          simp [hh, List.any_cons]
        · simp only [hh, Bool.false_eq_true, if_neg, ih, not_false_iff]
          simp [hh, List.any_cons]
    have := gen false
    simpa using this
  have any_char : (alts.any (fun t => t == st)) = true ↔ (∃ t ∈ alts, t = st) := by
    constructor
    · intro h
      rw [List.any_eq_true] at h
      obtain ⟨x, hx, hxeq⟩ := h
      exact ⟨x, hx, by simpa using hxeq⟩
    · rintro ⟨x, hx, hxeq⟩
      rw [List.any_eq_true]
      exact ⟨x, hx, by simp [hxeq]⟩
  unfold implementation_validateToken
  simp only [Id.run, bind, pure, Id.instMonad]
  rw [loop_lemma]
  unfold problem_spec_validateToken
  refine ⟨?_, ?_, ?_, ?_⟩
  · intro h; simp [h]
  · intro h1 h2
    simp only [h1] at *
    have hbeq : (st == ct) = true := by simp [h2]
    simp [hbeq]
  · intro h1 h2 h3
    have hbeq : (st == ct) = false := by simp [h2]
    have hne : (st != ([] : List Char)) = true := by simp [h1]
    have hany : (alts.any (fun t => t == st)) = true := any_char.mpr h3
    simp only [h1, hbeq, Bool.not_false, hne, hany, Bool.and_self]
    split <;> rfl
  · intro h1 h2 h3
    have hbeq : (st == ct) = false := by simp [h2]
    have hany : (alts.any (fun t => t == st)) = false := by
      by_contra hc
      have : (alts.any (fun t => t == st)) = true := by
        cases h : (alts.any (fun t => t == st)) with
        | false => exact absurd h hc
        | true => rfl
      exact h3 (any_char.mp this)
    simp only [h1, hbeq]
    simp [hany]

-- proof-end
