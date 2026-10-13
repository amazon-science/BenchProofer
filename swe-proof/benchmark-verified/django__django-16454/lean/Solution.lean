import Mathlib
-- imports-end

/-!
A command-line argument parser can spawn nested sub-parsers to dispatch
sub-commands. Such a parser carries a configuration flag that governs how it
reports argument errors to the user — for example, whether an invalid argument
yields a concise usage message or is surfaced directly as an exception.

When a parser constructs its sub-parsers, each sub-parser of the SAME family —
one that understands this configuration flag — should receive the parent's flag
value verbatim, so that argument-error reporting behaves consistently at every
nesting level. A sub-parser belonging to a FOREIGN family (one that does not
recognise the flag) receives nothing: the flag concept simply does not apply to
it.

The outcome is TOTAL: for any parent flag value and any requested sub-parser
family, construction yields a definite answer — either "a same-family sub-parser
carrying flag value v", or "a foreign sub-parser to which the flag does not
apply". It never fails to produce an answer.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The decision is a pure
-- computation over two inputs: whether the requested sub-parser family is the
-- same family that recognises the flag, and the parent's flag value. The
-- family test is modeled directly as a boolean input (a deep model of the
-- subclass relationship), and the downstream act of materialising the
-- sub-parser object is abstracted to the flag value the sub-parser ends up
-- carrying. Hence no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
-- (no shared helpers needed)
-- pure-end

-- post-conditions-start
/-- The outcome is TOTAL and fully pinned to the inputs.

  * When the requested sub-parser family is the SAME family that recognises the
    flag (`sameFamily = true`), the result is `some parentFlag`: a same-family
    sub-parser carrying EXACTLY the parent's flag value (`parentFlag : Option
    Bool`, where `none` is "flag unset", `some b` is the concrete value `b`).
  * When the requested family is FOREIGN (`sameFamily = false`), the result is
    `none`: the flag does not apply, and nothing is carried.

No output component is left free: the result is the exact function of the two
inputs, so both the family branch and the carried value are pinned. -/
def problem_spec_addSubparsers
    (sameFamily : Bool) (parentFlag : Option Bool)
    (result : Option (Option Bool)) : Prop :=
  result = (if sameFamily then some parentFlag else none)
-- post-conditions-end

-- impl-start
def implementation_addSubparsers
    (sameFamily : Bool) (parentFlag : Option Bool) :
    Option (Option Bool) := Id.run do
  -- The carried flag defaults to "not applicable"; only a same-family sub-parser
  -- is wired to receive the parent's flag value.
  let mut carried : Option (Option Bool) := none
  if sameFamily then
    carried := some parentFlag
  return carried
-- impl-end

-- proof-start
theorem correct_addSubparsers :
    ∀ (sameFamily : Bool) (parentFlag : Option Bool),
      problem_spec_addSubparsers sameFamily parentFlag
        (implementation_addSubparsers sameFamily parentFlag) := by
  intro sameFamily parentFlag
  unfold problem_spec_addSubparsers implementation_addSubparsers
  cases sameFamily <;> rfl
-- proof-end
