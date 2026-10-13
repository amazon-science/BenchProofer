import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here: the positional
-- single-field string template substitution is modeled DEEPLY (`formatFirst`,
-- below) rather than axiomatized, so its standard-library reference
-- implementation is validated as an A-reference by G-AX. The proof agent may
-- add `_prop` axioms only if stuck.
-- axioms-end

-- pure-start
/-- Substitute the replacement text into the FIRST positional placeholder
`{}` of a template, leaving the remainder of the template verbatim. A template
carrying exactly one placeholder yields the replacement spliced in at that
position; if there is no placeholder the template is returned unchanged. -/
def formatFirst : List Char → List Char → List Char
  | [], _ => []
  | '{' :: '}' :: rest, repl => repl ++ rest
  | c :: cs, repl => c :: formatFirst cs repl

/-- The relative URL that locates the password-change form for a record from the
record's own numeric identifier: two parent-directory steps, the decimal
identifier, then the `password` path segment. -/
def mkUrl (pk : Nat) : List Char :=
  "../../".toList ++ (toString pk).toList ++ "/password/".toList
-- pure-end

-- post-conditions-start
/-- The resulting help text is exactly the template with its single positional
placeholder replaced by the relative URL built from the record's own numeric
identifier (`mkUrl`); every other character of the template is preserved in
order. -/
def problem_spec_passwordHelpText
    (template : List Char) (pk : Nat) (result : List Char) : Prop :=
  result = formatFirst template (mkUrl pk)
-- post-conditions-end

-- impl-start
def implementation_passwordHelpText
    (template : List Char) (pk : Nat) : List Char := Id.run do
  let mut helpText := template
  let url := mkUrl pk
  helpText := formatFirst helpText url
  return helpText
-- impl-end

-- proof-start
theorem correct_passwordHelpText : ∀ (template : List Char) (pk : Nat),
    problem_spec_passwordHelpText template pk
      (implementation_passwordHelpText template pk) := by
  intro template pk
  unfold problem_spec_passwordHelpText implementation_passwordHelpText
  rfl
-- proof-end
