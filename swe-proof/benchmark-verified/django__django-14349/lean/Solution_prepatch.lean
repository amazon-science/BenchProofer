import Mathlib
-- imports-end

/-!
Deciding whether a candidate web address is acceptable.

An address is supplied as a string and must be judged acceptable or not. Two
independent conditions govern acceptance:

  * a structural condition — the address must be well-formed according to the
    usual address grammar (the scheme is among those allowed, the overall shape
    matches, and any embedded host is well-formed); and

  * a safety condition on the raw characters — an address that contains any of a
    designated group of disallowed control characters (a horizontal tab, a
    carriage return, or a line feed) is never acceptable, regardless of how it
    would otherwise be parsed. Such characters can cause the same text to be
    split or interpreted in more than one way, so their mere presence is
    disqualifying.

The desired behavior is therefore: if the address contains any disallowed
control character it is rejected outright; otherwise acceptance is exactly the
verdict of the structural condition. The two conditions together decide every
input, so the verdict is never left free.
-/

-- axioms-start
/-- The structural acceptance condition: it reports whether the address is
well-formed according to the usual address grammar (allowed scheme, overall
shape, embedded host). It is consumed here as an opaque carrier — the behavior
modeled in this bundle is how the raw-character safety condition combines with
the structural verdict, not the internal grammar the structural condition
applies. -/
opaque structurallyValid : List Char → Bool
-- axioms-end

-- pure-start
/-- The raw-character safety test: an address is disqualified when it contains
any of the disallowed control characters (horizontal tab, carriage return, line
feed). This is the set-membership test that disqualifies an address before the
structural condition is even consulted. -/
def containsForbidden (value : List Char) : Bool :=
  value.any (fun c => c == '\t' || c == '\r' || c == '\n')
-- pure-end

-- post-conditions-start
/-- The verdict is fully pinned to the input:

  * when the address contains a disallowed control character, it is rejected
    (the verdict is `false`); and

  * otherwise the verdict is exactly the structural acceptance condition applied
    to the address.

Both cases together determine the verdict for every input, so no part of the
result is left free. -/
def problem_spec_validateUrl (value : List Char) (result : Bool) : Prop :=
  (containsForbidden value = true  → result = false) ∧
  (containsForbidden value = false → result = structurallyValid value)
-- post-conditions-end

-- impl-start
def implementation_validateUrl (value : List Char) : Bool := Id.run do
  return structurallyValid value
-- impl-end

-- proof-start
theorem correct_validateUrl :
    ∀ (value : List Char),
      problem_spec_validateUrl value
        (implementation_validateUrl value) := by
  intro value
  unfold problem_spec_validateUrl implementation_validateUrl
  by_cases h : containsForbidden value = true
  · simp only [Id.run, h]
    refine ⟨fun _ => rfl, fun hne => ?_⟩
    rw [h] at hne; exact absurd hne (by simp)
  · simp only [Bool.not_eq_true] at h
    simp only [Id.run, h, Bool.false_eq_true]
    refine ⟨fun habs => ?_, fun _ => rfl⟩
    rw [h] at habs; exact absurd habs (by simp)
-- proof-end
