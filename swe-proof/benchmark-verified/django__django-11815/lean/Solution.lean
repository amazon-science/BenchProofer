import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The rendered reference text
-- is produced by substituting the carrier's parts into a constant literal
-- template; that substitution is reproduced concretely as an I op (an
-- order-preserving concatenation with literal punctuation), not abstracted behind
-- a model. The proof agent may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- The quoted form of an identifier: the identifier wrapped in single quotes.
A reference identifier (which contains no quote characters) is rendered as the
identifier surrounded by a single-quote on each side. -/
def quoted (s : List Char) : List Char := ['\''] ++ s ++ ['\'']
-- pure-end

-- post-conditions-start
/-- The rendered reference text for a member of an enumerated type. It is the
qualifying module path, a dot, the type name, then the member selected by its
*identifier* written as a quoted subscript: an opening bracket, the quoted
identifier, and a closing bracket — in that order. Every component is pinned to
its input: the text is determined entirely by the module path, the type name,
and the member identifier; it does NOT depend on the member's stored payload. -/
def problem_spec_serializeEnum
    (module className name : List Char) (result : List Char) : Prop :=
  result = module ++ ['.'] ++ className ++ ['['] ++ quoted name ++ [']']
-- post-conditions-end

-- impl-start
def implementation_serializeEnum
    (module className name payload : List Char) : List Char := Id.run do
  -- The member's stored payload is no longer consulted when forming the text;
  -- the member is referenced by its identifier as a quoted subscript.
  let _ := payload
  return module ++ ['.'] ++ className ++ ['['] ++ quoted name ++ [']']
-- impl-end

-- proof-start
theorem correct_serializeEnum :
    ∀ (module className name payload : List Char),
    problem_spec_serializeEnum module className name
      (implementation_serializeEnum module className name payload) := by
  intro module className name payload
  unfold problem_spec_serializeEnum implementation_serializeEnum
  rfl
-- proof-end
