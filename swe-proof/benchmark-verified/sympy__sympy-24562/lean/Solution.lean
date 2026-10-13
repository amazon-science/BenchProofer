import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The two operations this
-- behavior relies on — interpreting a decimal digit string as an integer, and
-- combining that integer with a whole-number factor — are modeled DEEPLY below
-- (a left-fold over the digit list and exact natural-number arithmetic), rather
-- than axiomatized, so their reference behavior is validated as A-references by
-- G-AX. The proof agent may add `_prop` axioms only if stuck.
-- axioms-end

-- pure-start
/-- Value of a decimal digit string, most-significant digit first:
`decval [d₀, d₁, …, dₖ] = ((…(d₀)·10 + d₁)…)·10 + dₖ`. Left-folding the digits
this way is exactly how a decimal numeral is read into an integer. -/
def decval (ds : List Nat) : Nat :=
  ds.foldl (fun acc d => acc * 10 + d) 0
-- pure-end

-- post-conditions-start
/-- Combine two pieces into a single denominator. The first piece, `pDen`, is a
positive whole-number factor already contributed by the first operand. The
second piece, `qdigits`, is a second operand supplied as a non-negative integer
written in positional decimal notation. The combined denominator is their
arithmetic product: the factor multiplied by the integer *value* of the decimal
operand — with no other dependence on how the operand was written, and with a
zero-valued operand zeroing the product. -/
def problem_spec_denominatorProduct
    (pDen : Nat) (qdigits : List Nat) (result : Nat) : Prop :=
  result = pDen * decval qdigits
-- post-conditions-end

-- impl-start
def implementation_denominatorProduct
    (pDen : Nat) (qdigits : List Nat) : Nat := Id.run do
  -- a FRESH integer accumulator for the combined denominator, started at 1 so
  -- that every contribution is combined numerically
  let mut denAcc : Nat := 1
  -- fold in the whole-number factor contributed by the first operand
  denAcc := denAcc * pDen
  -- the second operand is supplied as a decimal digit string: read it into the
  -- integer it denotes
  let mut c : Nat := 0
  for d in qdigits do
    c := c * 10 + d
  -- fold the operand's integer value into the same accumulator — including a
  -- zero value, which zeroes the combined result
  denAcc := denAcc * c
  return denAcc
-- impl-end

-- proof-start
/-- The desugared `forIn` loop accumulating decimal digits equals the left fold,
generalized over the starting accumulator (Route B helper). -/
theorem forIn_decval (qdigits : List Nat) (init : Nat) :
    Id.run (forIn qdigits init (fun d r => do
        pure PUnit.unit
        pure (ForInStep.yield (r * 10 + d)))) =
      qdigits.foldl (fun acc d => acc * 10 + d) init := by
  induction qdigits generalizing init with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    rw [List.foldl_cons]
    exact ih (init * 10 + a)

theorem correct_denominatorProduct :
    ∀ (pDen : Nat) (qdigits : List Nat),
      1 ≤ pDen → (∀ d ∈ qdigits, d < 10) →
      problem_spec_denominatorProduct pDen qdigits
        (implementation_denominatorProduct pDen qdigits) := by
  intro pDen qdigits _ _
  unfold problem_spec_denominatorProduct implementation_denominatorProduct decval
  have hb : Id.run (forIn qdigits 0 (fun d r => do
        pure PUnit.unit
        pure (ForInStep.yield (r * 10 + d)))) =
      qdigits.foldl (fun acc d => acc * 10 + d) 0 := forIn_decval qdigits 0
  simp only [Id.run, bind, pure] at hb ⊢
  rw [hb, Nat.one_mul]
-- proof-end
