import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here: the window-expression text
-- is rendered concretely as a literal-driven concatenation, and the numeric-cast
-- wrapper is likewise a concrete literal-driven concatenation. The branch that
-- selects WHAT gets cast is modeled DEEPLY (below) rather than axiomatized. The
-- proof agent may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- The rendered text of a windowed expression: the operand text, the keyword
` OVER (`, the assembled window-clause text, and a closing parenthesis, in that
exact order. This is the bare render used on every backend. -/
def windowedExpr (operand window : List Char) : List Char :=
  operand ++ " OVER (".toList ++ window ++ [')']
-- pure-end

-- post-conditions-start
/-- The rendered SQL of a windowed expression on a numeric-cast backend.

When the declared output type is a fixed-point decimal the *entire* windowed
expression is wrapped in a numeric cast `CAST(… AS NUMERIC)`, so the cast spans
the operand together with its `OVER (…)` clause as a single unit; otherwise the
bare windowed expression is rendered. Every unchanged component (operand text,
the `OVER (…)` clause, the window-clause text) is pinned to its input; only the
surrounding cast depends on the decimal-type flag. -/
def problem_spec_renderWindowSql
    (operand window : List Char) (isDecimal : Bool) (result : List Char) : Prop :=
  result =
    if isDecimal then
      "CAST(".toList ++ windowedExpr operand window ++ " AS NUMERIC)".toList
    else
      windowedExpr operand window
-- post-conditions-end

-- impl-start
def implementation_renderWindowSql
    (operand window : List Char) (isDecimal : Bool) : List Char := Id.run do
  -- Pre-patch (buggy): the numeric cast wraps only the operand, leaving the
  -- `OVER (…)` clause dangling outside the cast.
  let mut inner : List Char := operand
  if isDecimal then
    inner := "CAST(".toList ++ operand ++ " AS NUMERIC)".toList
  return inner ++ " OVER (".toList ++ window ++ [')']
-- impl-end

-- proof-start
theorem correct_renderWindowSql :
    ∀ (operand window : List Char) (isDecimal : Bool),
    problem_spec_renderWindowSql operand window isDecimal
      (implementation_renderWindowSql operand window isDecimal) := by
  intro operand window isDecimal
  unfold problem_spec_renderWindowSql implementation_renderWindowSql windowedExpr
  cases isDecimal <;> rfl
-- proof-end
