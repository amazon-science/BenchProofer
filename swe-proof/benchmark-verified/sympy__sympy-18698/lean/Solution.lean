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
    let mut result : List (Int × Nat) := []
    for k in (factors.map Prod.snd).dedup do
      let mut prod : Int := 1
      for fk in factors do
        if fk.2 = k then
          prod := prod * fk.1
      result := result ++ [(prod, k)]
    return result
-- impl-end

-- proof-start
/-- The inner loop folds the matching factors' products onto the accumulator;
generalised over the accumulator so it reduces to `List.foldl` over the filtered
list (matching `prodOf`). -/
theorem inner_combineFactors_helper
    (factors : List (Int × Nat)) (k : Nat) (init : Int) :
    (Id.run (forIn factors init (fun fk r =>
        (if fk.2 = k then pure (ForInStep.yield (r * fk.1))
         else pure (ForInStep.yield r) : Id (ForInStep Int)))))
    = (factors.filter (fun fk => fk.2 = k)).foldl (fun acc fk => acc * fk.1) init := by
  induction factors generalizing init with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : a.2 = k <;> simp [h, ih]

/-- The outer loop appends one `(prodOf factors k, k)` entry per multiplicity;
generalised over the accumulator so it reduces to a `List.map`. -/
theorem outer_combineFactors_helper
    (factors : List (Int × Nat)) (ks : List Nat) (init : List (Int × Nat)) :
    (Id.run (forIn ks init (fun k r =>
        (do
          let prod ← (forIn factors (1:Int) (fun fk r =>
              (if fk.2 = k then pure (ForInStep.yield (r * fk.1))
               else pure (ForInStep.yield r) : Id (ForInStep Int))))
          pure (ForInStep.yield (r ++ [(prod, k)])) : Id (ForInStep (List (Int × Nat)))))))
    = init ++ ks.map (fun k => (prodOf factors k, k)) := by
  induction ks generalizing init with
  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    rw [show (forIn factors (1:Int) (fun fk r =>
              (if fk.2 = a then pure (ForInStep.yield (r * fk.1))
               else pure (ForInStep.yield r) : Id (ForInStep Int))))
        = Id.run (forIn factors (1:Int) (fun fk r =>
              (if fk.2 = a then pure (ForInStep.yield (r * fk.1))
               else pure (ForInStep.yield r) : Id (ForInStep Int)))) from rfl]
    rw [inner_combineFactors_helper, ih]
    simp [prodOf, List.map_cons]

/-- Closed form of the imperative implementation. -/
theorem hbody_combineFactors (factors : List (Int × Nat)) :
    implementation_combineFactors factors
      = (factors.map Prod.snd).dedup.map (fun k => (prodOf factors k, k)) := by
  unfold implementation_combineFactors
  simp only [Id.run]
  -- bridge the desugared body (`do pure PUnit.unit; …`) to the clean helper body
  have h2 : (forIn (factors.map Prod.snd).dedup ([] : List (Int × Nat)) fun k r =>
        (do
          let r_1 ← (forIn factors (1:Int) fun fk r =>
              (if fk.2 = k then do pure PUnit.unit; pure (ForInStep.yield (r * fk.1))
               else do pure PUnit.unit; pure (ForInStep.yield r) : Id (ForInStep Int)))
          pure PUnit.unit
          pure (ForInStep.yield (r ++ [(r_1, k)])) : Id (ForInStep (List (Int × Nat)))))
      = (forIn (factors.map Prod.snd).dedup ([] : List (Int × Nat)) fun k r =>
        (do
          let prod ← (forIn factors (1:Int) fun fk r =>
              (if fk.2 = k then pure (ForInStep.yield (r * fk.1))
               else pure (ForInStep.yield r) : Id (ForInStep Int)))
          pure (ForInStep.yield (r ++ [(prod, k)])) : Id (ForInStep (List (Int × Nat))))) := rfl
  rw [h2]
  simp only [bind_pure]
  show (Id.run _ : List (Int × Nat)) = _
  rw [outer_combineFactors_helper]
  simp

theorem correct_combineFactors :
    ∀ (factors : List (Int × Nat)),
      problem_spec_combineFactors factors (implementation_combineFactors factors) := by
  intro factors
  have key : (implementation_combineFactors factors).map Prod.snd
      = (factors.map Prod.snd).dedup := by
    rw [hbody_combineFactors, List.map_map]
    exact List.map_id _
  refine ⟨?_, ?_, ?_⟩
  · -- multiplicity column is `Nodup` (it is a `dedup`)
    rw [key]; exact (factors.map Prod.snd).nodup_dedup
  · -- the result's multiplicities are exactly the input's
    intro k; rw [key]; exact List.mem_dedup
  · -- each entry's factor is the product of the matching inputs
    intro p k hmem
    rw [hbody_combineFactors] at hmem
    simp only [List.mem_map] at hmem
    obtain ⟨k', _, hk'⟩ := hmem
    rw [Prod.ext_iff] at hk'
    obtain ⟨hp, hk⟩ := hk'
    simp only at hp hk
    rw [← hp, ← hk]
-- proof-end
