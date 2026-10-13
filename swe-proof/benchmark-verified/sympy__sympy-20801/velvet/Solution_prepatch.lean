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
    -- Pre-image skeleton: the zero value short-circuits FIRST, before the
    -- operand kind is examined, returning the negation of the operand's truth
    -- value for every kind. This makes a zero value compared with a falsy
    -- logical constant report equality (the negation of a falsy operand is
    -- true), so prove_correct MUST fail against the frozen spec.
    let otherTruth : Bool :=
      match o with
      | .logical b   => b
      | .numeric m   => decide (m ≠ 0)
      | .symbolic t  => t
    if selfVal = 0 then
      pure (!otherTruth)
    else
      match o with
      | .logical _   => pure false
      | .numeric m   => pure (decide (selfVal = m))
      | .symbolic _  => pure false
    -- impl-end

prove_correct equalsOperand by
  loom_solve
