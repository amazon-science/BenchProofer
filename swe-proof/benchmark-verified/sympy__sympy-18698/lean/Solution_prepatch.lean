import Mathlib
-- imports-end

/-!
Consolidating a list of factors tagged by multiplicity.

The input is a list of `(factor, multiplicity)` pairs.  Several distinct factors
may carry the *same* multiplicity.  The desired result lists each multiplicity
that occurs **exactly once**, pairing it with the product of all the input
factors that carried that multiplicity.  No multiplicity that occurs in the
input is dropped, and none is invented; for every retained multiplicity the
accompanying factor is precisely the product of the input factors sharing it.

A factor is modelled as an element of a commutative monoid (here the integers
under multiplication); "combining" factors is taking their product.  The order
in which the consolidated entries are returned is not part of the contract — a
consumer re-orders them — so the result is pinned as a set: which multiplicities
appear, that each appears only once, and what product accompanies each.
-/

-- axioms-start
-- No unchanged outside callee is consumed.  The consolidation is modelled
-- deeply: the product accompanying a multiplicity is spelled out as the fold of
-- the matching input factors, so there is no `opaque`/`axiom` callee contract.
-- axioms-end

-- pure-start
/-- The product of every input factor whose multiplicity equals `k`
(`1` when none match).  Matches the inner accumulating loop of the
implementation: filter to the matching pairs, then fold their factors. -/
def prodOf (factors : List (Int × Nat)) (k : Nat) : Int :=
  (factors.filter (fun fk => fk.2 = k)).foldl (fun acc fk => acc * fk.1) 1
-- pure-end

-- post-conditions-start
/-- The consolidated factor list, pinned as a set:

  * each multiplicity appears at most once (`Nodup` on the multiplicity column);
  * the multiplicities appearing in the result are exactly those appearing in
    the input (none dropped, none invented);
  * every result entry pairs a multiplicity `k` with the product of all input
    factors carrying that multiplicity.

Together these determine the result uniquely up to ordering. -/
def problem_spec_combineFactors
    (factors : List (Int × Nat)) (result : List (Int × Nat)) : Prop :=
  (result.map Prod.snd).Nodup
  ∧ (∀ k, k ∈ result.map Prod.snd ↔ k ∈ factors.map Prod.snd)
  ∧ (∀ p k, (p, k) ∈ result → p = prodOf factors k)
-- post-conditions-end

-- impl-start
def implementation_combineFactors (factors : List (Int × Nat)) : List (Int × Nat) :=
  Id.run do
    -- pre-patch behaviour: the factor list is returned without consolidating
    -- entries that share a multiplicity.
    return factors
-- impl-end

-- proof-start
theorem correct_combineFactors :
    ∀ (factors : List (Int × Nat)),
      problem_spec_combineFactors factors (implementation_combineFactors factors) := by
  sorry
-- proof-end
