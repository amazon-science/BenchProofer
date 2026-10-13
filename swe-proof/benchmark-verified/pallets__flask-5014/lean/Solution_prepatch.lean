import Mathlib
-- imports-end

/-!
Constructing a named registrable component from a caller-supplied name.

A name is subject to two validity requirements: it must be present (a non-empty
string), and it must not contain a dot `.` character (the dot is reserved as a
hierarchy separator). Construction is an input→output relation: given a name, it
either fails — exactly when the name is empty, or when it contains a dot — or
succeeds, yielding a component that records the supplied name unchanged.

This is stated abstractly as an input→output relation; the implementation and
correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the validation is modeled
-- deeply with concrete operations (an emptiness test, a dot-membership test, and
-- a field assignment). The orthogonal base-class initialization that stores the
-- other, untouched attributes is abstracted out of the modeled state.
-- axioms-end

-- pure-start
/-- The two distinct validity failures observable here. -/
inductive BPError where
  | emptyName
  | dottedName
deriving DecidableEq, Repr

/-- A constructed component, carrying only the field this validation touches:
the supplied name. -/
structure BPState where
  name : String
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- Construction fails with the emptiness failure exactly when the name is
empty; otherwise it fails with the dot failure exactly when the name contains a
dot character; otherwise it succeeds, recording the supplied name unchanged. -/
def problem_spec_construct (name : String) (result : Except BPError BPState) : Prop :=
  if name = "" then
    result = Except.error BPError.emptyName
  else if name.contains '.' then
    result = Except.error BPError.dottedName
  else
    result = Except.ok { name := name }
-- post-conditions-end

-- impl-start
-- PRE-PATCH skeleton: only the dot-character requirement is enforced. An empty
-- name is NOT rejected — it falls through to a successful construction, even
-- though the desired behavior fails it.
def implementation_construct (name : String) : Except BPError BPState := Id.run do
  if name.contains '.' then
    return Except.error BPError.dottedName
  let st : BPState := { name := name }
  return Except.ok st
-- impl-end

-- proof-start
-- Gold proof body carried over from Solution.lean (SPEC_GUIDE §1.1). Against
-- this impl it cannot close: for the empty name the spec requires the emptiness
-- failure (`Except.error BPError.emptyName`) while this impl yields successful
-- construction (`Except.ok { name := "" }`).
theorem correct_construct :
    ∀ (name : String),
      problem_spec_construct name (implementation_construct name) := by
  intro name
  unfold problem_spec_construct implementation_construct
  simp only [Id.run, Id.pure_eq, Id.bind_eq]
  by_cases h1 : name = ""
  · simp [h1]
  · by_cases h2 : name.contains '.' = true
    · simp [h1, h2]
    · simp [h1, h2]
-- proof-end
