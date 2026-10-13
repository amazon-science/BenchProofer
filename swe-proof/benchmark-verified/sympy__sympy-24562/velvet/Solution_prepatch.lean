import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed callee contracts and no A-reference deep model. The two inputs —
--  the denominator factor contributed by the first operand, and the second
--  operand presented as a non-negative integer in positional decimal notation —
--  are the observable results of UNCHANGED parsing/normalisation callees run on
--  the raw operands before this step; they are abstracted as read-only inputs.
--  The operation under specification — assembling the combined denominator from
--  those two pieces — is modeled deeply below as the do block. Nothing is
--  borrowed from an outside contract, so there is no axiom to validate.)
-- axioms-end

-- pure-start
/- The non-negative integer denoted by a sequence of decimal digits read in the
   usual most-significant-first order: each further digit shifts the running
   value one decimal place and adds the digit. `[]` denotes 0. This is the value
   of an integer presented in positional decimal notation. -/
def digitsValue (ds : List Nat) : Nat :=
  ds.foldl (fun acc d => acc * 10 + d) 0
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Combine two pieces into a single denominator. The first piece, `pDen`, is a
   positive whole-number factor already contributed by the first operand. The
   second piece, `qDigits`, is a second operand supplied as a non-negative
   integer written in positional decimal notation. The combined denominator is
   their arithmetic product: the factor multiplied by the integer *value* of the
   decimal operand.

   The decimal operand must be combined by its numeric VALUE — a denominator of
   `pDen` factors of one whole number times the value of the other. It must not
   be combined by any other reading of its digit sequence.

   `pDen` and `qDigits` are read-only (not `mut`); the step builds a fresh
   result and mutates neither input (directive 5). -/
method denominatorProduct (pDen : Nat) (qDigits : List Nat)
    return (out : Nat)
  require pDen ≥ 1
  require ∀ d ∈ qDigits, d < 10
  ensures out = pDen * digitsValue qDigits
  do
    -- impl-start
    -- Pre-image skeleton: instead of reading the decimal operand for its value
    -- and multiplying, the raw decimal operand is itself "scaled" by the factor
    -- — its digit sequence is laid down `pDen` times end to end, and the value
    -- of that lengthened digit sequence is taken as the denominator (the model
    -- of scaling a still-textual operand: repeating, not multiplying). This MUST
    -- fail the value-product postcondition.
    let scaled := (List.replicate pDen qDigits).flatten
    return digitsValue scaled
    -- impl-end

prove_correct denominatorProduct by
  loom_solve
