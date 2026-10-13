import Mathlib
-- imports-end

-- axioms-start
/-- A safe, size-limited textual representation of a parameter value: it always
produces text (even for non-textual values, where a plain textual coercion would
be unsafe) and keeps the result within the reporter's built-in size budget.
Declared opaque — its internal formatting and its exact budget are irrelevant
here; the modeled behavior only depends on the fact that this canonical
representation is the one applied to the parameter. -/
opaque safeDisplay : List Char → List Char
-- axioms-end

-- pure-start
-- (no pure helpers needed)
-- pure-end

-- post-conditions-start
/-- The text emitted for a fixture action is the unchanged header, followed — only
when the action carries a parameter value — by that value's safe, size-limited
representation enclosed in square brackets. When no parameter value is present
the emitted text is exactly the header, unchanged. -/
def problem_spec_actionLine (header : List Char) (param : Option (List Char))
    (result : List Char) : Prop :=
  match param with
  | none   => result = header
  | some p => result = header ++ ['['] ++ safeDisplay p ++ [']']
-- post-conditions-end

-- impl-start
-- Pre-patch skeleton: the parameter value is inserted verbatim (a plain textual
-- coercion of the value), with no safe, size-limited representation applied.
def implementation_actionLine (header : List Char) (param : Option (List Char)) :
    List Char := Id.run do
  let mut out := header
  match param with
  | some p => out := out ++ ['['] ++ p ++ [']']
  | none   => pure ()
  return out
-- impl-end

-- proof-start
theorem correct_actionLine : ∀ (header : List Char) (param : Option (List Char)),
    problem_spec_actionLine header param (implementation_actionLine header param) := by
  sorry   -- carries the gold proof body; UNCLOSABLE against the buggy impl (G-DIFF)
-- proof-end
