import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The combined predicate is
-- modeled DEEPLY at the level of its boolean semantics: the disjunction of the
-- operands, the count of true operands, the parity/equality test on that count,
-- and the final conjunction are all reproduced concretely as ordinary boolean
-- and arithmetic operations rather than axiomatized. The proof agent may add
-- `_prop` axioms only if it gets genuinely stuck.
-- axioms-end

-- pure-start
/-- The number of operands whose condition holds, taken over the list of operand
truth values. -/
def countTrue (cs : List Bool) : Nat :=
  (cs.filter (fun b => b)).length
-- pure-end

-- post-conditions-start
/-- Boolean semantics of the combined predicate built from a list of operand
truth values `cs`. The combined predicate must be true exactly when an odd number
of the operands are true (the meaning of an n-ary exclusive-or). The whole output
is pinned to this single parity relation on the inputs; nothing is left free. -/
def problem_spec_xorFallback (cs : List Bool) (result : Bool) : Prop :=
  result = (countTrue cs % 2 == 1)
-- post-conditions-end

-- impl-start
def implementation_xorFallback (cs : List Bool) : Bool := Id.run do
  -- Pre-patch (buggy): the running sum is always compared directly to one, so the
  -- combined predicate is true only when EXACTLY one operand is true — wrong for
  -- more than two operands, where an odd count (3, 5, …) should hold.
  let mut lhs := false
  for c in cs do
    lhs := lhs || c
  let mut rhsSum : Nat := 0
  for c in cs do
    if c then
      rhsSum := rhsSum + 1
  let mut rhs := false
  rhs := (rhsSum == 1)
  return lhs && rhs
-- impl-end

-- proof-start
theorem correct_xorFallback :
    ∀ (cs : List Bool),
    problem_spec_xorFallback cs (implementation_xorFallback cs) := by
  intro cs
  unfold problem_spec_xorFallback implementation_xorFallback countTrue
  -- carries the gold proof intent; UNCLOSABLE against the buggy impl (G-DIFF):
  -- at cs = [true, true, true] the impl yields false but the spec demands true.
  rfl
-- proof-end
