import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- A right-hand operand of an equality test against a finite-precision value,
   classified by the three kinds the test distinguishes:
   * `logical b` — a logical constant carrying its truth value `b`;
   * `numeric m` — a number, carrying its exact value `m` at the left value's
     precision (the comparison between numbers is exact);
   * `symbolic t` — any other expression that is neither a logical constant nor
     a number, carrying its truth value `t`. -/
inductive Operand where
  | logical (b : Bool)
  | numeric (m : Int)
  | symbolic (t : Bool)

/- The equality of a finite-precision value `selfVal` (its exact value; the
   zero value is `0`) with a classified operand:

   * against a logical constant the values are of incomparable kind, so they are
     never equal;
   * against a number, equality is the exact equality of values;
   * against any other expression, equality holds exactly when the value is the
     zero value and the expression is falsy.

   This is the abstract behavior the test must realize, expressed structurally
   over the inputs (no opaque oracle). -/
@[grind] def floatEq (selfVal : Int) (o : Operand) : Bool :=
  match o with
  | .logical _   => false
  | .numeric m   => decide (selfVal = m)
  | .symbolic t  => if selfVal = 0 then !t else false
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method equalsOperand (selfVal : Int) (o : Operand) return (out : Bool)
  ensures out = floatEq selfVal o
  do
    -- impl-start
    -- Dispatch on the operand kind, in the kind order the test uses:
    -- a logical constant is settled first (never equal); a number is settled by
    -- exact value equality; any other expression is equal only when the value
    -- is the zero value and the expression is falsy.
    match o with
    | .logical _   => pure false
    | .numeric m   => pure (decide (selfVal = m))
    | .symbolic t  => pure (if selfVal = 0 then !t else false)
    -- impl-end

prove_correct equalsOperand by
  loom_solve
