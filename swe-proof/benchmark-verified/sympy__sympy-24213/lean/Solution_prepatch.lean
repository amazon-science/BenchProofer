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
    if dim.name ≠ a.2.name then
      return none
    factor := factor + a.1
  return some (factor, dim)
-- impl-end

-- proof-start
theorem correct_factorAndDimensionOfSum
    (head : Rat × Dim) (addends : List (Rat × Dim)) :
    problem_spec_factorAndDimensionOfSum head addends
      (implementation_factorAndDimensionOfSum head addends) := by
  -- Carried gold proof intent: reduce the loop to the `deps`-keyed fold via the
  -- accumulator-generalized helper. UNCLOSABLE against an impl that branches on
  -- `name` instead of `deps` (the discriminating clause), so this fails
  -- verification (G-DIFF).
  unfold problem_spec_factorAndDimensionOfSum implementation_factorAndDimensionOfSum
    allDimsMatch summedFactor
  simp only [Id.run]
  suffices h : ∀ (init : Rat),
      (Id.run do
        let r ← forIn addends (⟨none, init⟩ : Option (Option (Rat × Dim)) × Rat) fun a r =>
              if head.2.deps ≠ a.2.deps then pure (ForInStep.done ⟨some none, r.snd⟩)
              else (do pure PUnit.unit; pure PUnit.unit;
                       pure (ForInStep.yield ⟨none, r.snd + a.1⟩))
        match r.fst with
          | none => (do pure PUnit.unit; pure (some (r.snd, head.2)))
          | some a => pure a)
        = (if addends.all (fun a => decide (a.2.deps = head.2.deps)) then
              some (init + (addends.map Prod.fst).sum, head.2) else none) by
    have := h head.1
    simpa using this
  intro init
  induction addends generalizing init with
  | nil => simp [Id.run]
  | cons x xs ih =>
    rw [List.forIn_cons]
    by_cases hx : head.2.deps = x.2.deps
    · have hne : ¬ (head.2.deps ≠ x.2.deps) := by simp [hx]
      simp only [Id.run, bind, hne, if_false] at ih ⊢
      rw [ih]
      have hdec : decide (x.2.deps = head.2.deps) = true := by simp [hx, Eq.comm]
      simp only [List.all_cons, hdec, Bool.true_and, List.map_cons, List.sum_cons]
      by_cases hall : xs.all (fun a => decide (a.2.deps = head.2.deps)) = true
      · simp only [hall, if_true, add_assoc]
      · simp only [hall, Bool.false_eq_true, if_false]
    · have hdec : decide (x.2.deps = head.2.deps) = false := by
        simp only [decide_eq_false_iff_not]; exact fun hh => hx hh.symm
      simp only [Id.run, bind, hx, ne_eq, not_false_iff, if_true,
        List.all_cons, hdec, Bool.false_and, Bool.false_eq_true, if_false]
-- proof-end
