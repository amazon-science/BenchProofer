import Mathlib
-- imports-end

/-!
Validating the entry a user supplies at the "enter a new root path (or just
Enter to exit)" prompt.

The entry is interpreted as follows:

  * an EMPTY entry is accepted verbatim — the caller reads back the empty value
    and treats it as the user declining to supply a path (so the surrounding
    flow can stop);
  * a NON-EMPTY entry must name an existing directory: it is handed to the
    standard existing-directory validator, which either returns the validated
    entry or reports a validation error.

We model the validator's result as `Except String String`: a `.ok s` is an
accepted entry `s`; a `.error m` is a validation error with message `m`. The
existing-directory validator is an unchanged input routine, modeled as an opaque
callee `checkExistingDir` so it appears identically in the specification and the
implementation; the specification pins only WHICH entries reach it.
-/

-- axioms-start
-- The existing-directory validator is an UNCHANGED library routine: given a
-- candidate entry it returns the validated entry (`.ok`) or a validation error
-- (`.error`). It is modeled as an opaque callee so the same routine appears in
-- both the specification and the implementation (an A-reference that cancels in
-- the differential), since the behavior of interest is WHICH entries are routed
-- to it, not what it computes. No property of this callee is consumed by the
-- proof, so no `axiom … _prop` is declared.
opaque checkExistingDir : String → Except String String
-- axioms-end

-- pure-start
-- (No additional pure helpers are needed.)
-- pure-end

-- post-conditions-start
/-- The validated result for an entry `x`. An empty entry is accepted verbatim
(`.ok x`, i.e. `.ok ""`); a non-empty entry yields exactly the existing-directory
validator's result for that entry. Every case is pinned to the input. -/
def problem_spec_validateRootEntry
    (x : String) (result : Except String String) : Prop :=
  (x = "" → result = Except.ok x) ∧
  (x ≠ "" → result = checkExistingDir x)
-- post-conditions-end

-- impl-start
def implementation_validateRootEntry (x : String) : Except String String :=
  Id.run do
    if x == "" then
      return Except.ok x
    return checkExistingDir x
-- impl-end

-- proof-start
theorem correct_validateRootEntry :
    ∀ (x : String),
      problem_spec_validateRootEntry x (implementation_validateRootEntry x) := by
  intro x
  unfold problem_spec_validateRootEntry implementation_validateRootEntry
  by_cases h : x = ""
  · subst h
    refine ⟨fun _ => rfl, fun hx => absurd rfl hx⟩
  · have hne : (x == "") = false := by
      simp [beq_eq_false_iff_ne, h]
    refine ⟨fun hx => absurd hx h, fun _ => ?_⟩
    simp only [Id.run, hne]
    rfl
-- proof-end
