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
def implementation_construct (name : String) : Except BPError BPState := Id.run do
  if name = "" then
    return Except.error BPError.emptyName
  if name.contains '.' then
    return Except.error BPError.dottedName
  let st : BPState := { name := name }
  return Except.ok st
-- impl-end

-- proof-start
theorem correct_construct :
    ∀ (name : String),
      problem_spec_construct name (implementation_construct name) := by
  intro name
  unfold problem_spec_construct implementation_construct
  by_cases he : name = ""
  · simp only [Id.run, he, if_true]; rfl
  · by_cases hd : name.contains '.'
    · simp only [Id.run, he, hd, if_false, if_true]; rfl
    · simp only [Id.run, he, hd, if_false]; rfl
-- proof-end
