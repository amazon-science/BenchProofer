import Mathlib
-- imports-end

/-!
Combining the scale factor and the dimension of a *sum* of dimensional
quantities.

A dimensional quantity carries a rational scale factor together with a
dimension. A dimension is described two ways at once: by its surface symbolic
identity (`name`), and by its canonical reduction to integer powers of base
dimensions (`deps`, an association list pairing each base dimension with its
exponent). Two dimensions are considered the *same physical dimension* exactly
when these canonical base-dimension power maps coincide — even when their
surface identities are written differently (for instance a quantity recorded
directly as one dimension versus the product of two others that reduces to the
same base powers).

Forming the sum requires all addends to share the head addend's physical
dimension. The combination is computed by taking the head addend's
`(scaleFactor, dimension)` and folding the remaining addends in left-to-right
order: each remaining addend is required to have the *same physical dimension*
as the head — comparison is on the canonical base-dimension power map, so two
differently-written but physically equal dimensions are accepted — and when it
does, its scale factor is added to the running total. If any addend's physical
dimension differs from the head's, the sum is undefined (no result). When every
addend matches, the result is the total scale factor paired with the head
addend's dimension (the dimension component is carried through unchanged).
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The
-- physical-dimension comparison is modeled DEEPLY: a dimension is paired with
-- its canonical base-dimension power map (`deps`), and "same physical
-- dimension" is equality of those maps. Rational scale-factor addition is the
-- field operation on `Rat`. No `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A dimension, described both by its surface symbolic identity (`name`) and by
its canonical reduction to integer powers of base dimensions (`deps`, an
association list base-dimension ↦ exponent). Two dimensions denote the same
physical dimension exactly when their `deps` maps coincide. The `deps` list is
canonical: sorted by key with no zero exponents, so list equality is map
equality. -/
structure Dim where
  name : String
  deps : List (String × Int)
deriving DecidableEq, Repr

/-- The combined scale factor when every addend shares the head's physical
dimension: the head's factor plus the sum of all addend factors. -/
def summedFactor (head : Rat × Dim) (addends : List (Rat × Dim)) : Rat :=
  head.1 + (addends.map Prod.fst).sum

/-- All addends share the head addend's physical dimension (canonical
base-dimension power maps coincide). -/
def allDimsMatch (head : Rat × Dim) (addends : List (Rat × Dim)) : Bool :=
  addends.all (fun a => decide (a.2.deps = head.2.deps))
-- pure-end

-- post-conditions-start
/-- The outcome of combining a sum's addends. When every addend shares the head
addend's physical dimension — compared via the canonical base-dimension power
map — the result is `some (totalFactor, headDimension)`: the summed scale factor
paired with the head addend's dimension carried through unchanged. When any
addend's physical dimension differs from the head's, there is no result
(`none`). -/
def problem_spec_factorAndDimensionOfSum
    (head : Rat × Dim) (addends : List (Rat × Dim))
    (result : Option (Rat × Dim)) : Prop :=
  result =
    (if allDimsMatch head addends then
        some (summedFactor head addends, head.2)
      else
        none)
-- post-conditions-end

-- impl-start
def implementation_factorAndDimensionOfSum
    (head : Rat × Dim) (addends : List (Rat × Dim)) :
    Option (Rat × Dim) := Id.run do
  let dim := head.2
  let mut factor := head.1
  for a in addends do
    if dim.deps ≠ a.2.deps then
      return none
    factor := factor + a.1
  return some (factor, dim)
-- impl-end


-- proof-start
theorem correct_factorAndDimensionOfSum
    (head : Rat × Dim) (addends : List (Rat × Dim)) :
    problem_spec_factorAndDimensionOfSum head addends
      (implementation_factorAndDimensionOfSum head addends) := by
  simp only [problem_spec_factorAndDimensionOfSum, implementation_factorAndDimensionOfSum,
    Id.run, allDimsMatch, summedFactor]
  generalize head.1 = c
  induction addends generalizing c with
  | nil => simp; rfl
  | cons a as ih =>
    simp only [List.forIn_cons, List.all_cons, List.map_cons, List.sum_cons]
    by_cases h : head.2.deps = a.2.deps
    · simp only [ne_eq, not_true_eq_false, decide_true, Bool.true_and, reduceIte,
        pure_bind, h] at ih ⊢
      rw [ih]
      by_cases h2 : (as.all fun x => decide (x.2.deps = a.2.deps)) = true <;>
        simp only [h2, if_true] <;> [skip; rfl] <;> congr 2 <;> ring
    · rw [if_pos h, if_neg (by
        simp only [Bool.and_eq_true, decide_eq_true_eq, not_and]
        intro hcon _; exact absurd hcon.symm h)]
      rfl

-- proof-end
