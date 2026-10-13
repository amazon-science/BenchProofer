import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here: the SQL-fragment assembly
-- is rendered concretely as a literal-driven concatenation, and the DISTINCT
-- modifier text is modeled DEEPLY (below) rather than axiomatized. The proof
-- agent may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- The DISTINCT modifier fragment emitted before the argument text. When the
modifier is requested the keyword is followed by a single space so it is kept
separate from whatever argument text follows it; otherwise the fragment is
empty. -/
def distinctKeyword (distinct : Bool) : List Char :=
  if distinct then "DISTINCT ".toList else []
-- pure-end

-- post-conditions-start
/-- The rendered call text is exactly the function name, an opening parenthesis,
the DISTINCT modifier fragment, the argument text, and a closing parenthesis, in
that order. Every unchanged component (function name, parentheses, argument text)
is pinned to its input; only the modifier fragment depends on the flag. -/
def problem_spec_buildCallSql
    (function : List Char) (distinct : Bool) (expressions : List Char)
    (result : List Char) : Prop :=
  result = function ++ ['('] ++ distinctKeyword distinct ++ expressions ++ [')']
-- post-conditions-end

-- impl-start
def implementation_buildCallSql
    (function : List Char) (distinct : Bool) (expressions : List Char) :
    List Char := Id.run do
  -- Pre-patch (buggy): the DISTINCT modifier carries no trailing separator, so it
  -- runs straight into the following argument text.
  let mut distinctSlot : List Char := []
  if distinct then
    distinctSlot := "DISTINCT".toList
  return function ++ ['('] ++ distinctSlot ++ expressions ++ [')']
-- impl-end

-- proof-start
theorem correct_buildCallSql :
    ∀ (function : List Char) (distinct : Bool) (expressions : List Char),
    problem_spec_buildCallSql function distinct expressions
      (implementation_buildCallSql function distinct expressions) := by
  sorry   -- carries the gold proof body; UNCLOSABLE against the buggy impl (G-DIFF)
-- proof-end
