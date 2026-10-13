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
/-- Pre-patch (buggy) skeleton: the whole-number factor is folded into the
*textual* operand rather than a numeric accumulator. Concretely, the operand's
digit string is duplicated as many times as the factor before being read as a
number — so the operand's written form is repeated instead of its value being
multiplied. This produces a combined denominator far larger than the intended
one whenever the factor exceeds 1 and the operand is nonzero. -/
def implementation_denominatorProduct
    (pDen : Nat) (qdigits : List Nat) : Nat := Id.run do
  -- duplicate the operand's digit string `pDen` times (textual repetition)
  let mut digits : List Nat := []
  for _ in [0:pDen] do
    digits := digits ++ qdigits
  -- only now read the (repeated) digit string into an integer
  let mut c : Nat := 0
  for d in digits do
    c := c * 10 + d
  return c
-- impl-end

-- proof-start
theorem correct_denominatorProduct :
    ∀ (pDen : Nat) (qdigits : List Nat),
      1 ≤ pDen → (∀ d ∈ qdigits, d < 10) →
      problem_spec_denominatorProduct pDen qdigits
        (implementation_denominatorProduct pDen qdigits) := by
  sorry   -- carries the gold proof body; UNCLOSABLE against the buggy impl (G-DIFF)
-- proof-end
