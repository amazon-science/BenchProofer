import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature: the per-entry label lookup is
-- modeled DEEPLY (a total list index, below) rather than axiomatized. The proof
-- agent may add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- A designated sentinel index value that marks an entry having no associated
name (as opposed to a genuine, in-range position into the name list). -/
def sentinelIndex : Int := -2

/-- Resolve one index against the name list. A sentinel index yields no name
(`none`); any other index looks the name up by position, yielding `some name`
when it is in range. -/
def featureNameAt (featureNames : List String) (i : Int) : Option String :=
  if i ≠ sentinelIndex then featureNames[i.toNat]? else none

/-- Front-recursive specification fold: resolve each index in order. -/
def featureNamesSpec (featureNames : List String) : List Int → List (Option String)
  | [] => []
  | i :: rest => featureNameAt featureNames i :: featureNamesSpec featureNames rest
-- pure-end

-- post-conditions-start
/-- The result is exactly the per-entry resolution of the index list against the
name list, in order: an entry whose index is the sentinel resolves to no name
(`none`), and every other entry resolves to the name at that position. -/
def problem_spec_featureNamesByNode
    (featureNames : List String) (features : List Int)
    (result : List (Option String)) : Prop :=
  result = featureNamesSpec featureNames features
-- post-conditions-end

-- impl-start
def implementation_featureNamesByNode
    (featureNames : List String) (features : List Int) : List (Option String) :=
  Id.run do
    let mut acc : List (Option String) := []
    for i in features do
      if i ≠ sentinelIndex then
        acc := acc ++ [featureNames[i.toNat]?]
      else
        acc := acc ++ [none]
    return acc
-- impl-end

-- proof-start
/-- Helper (Route B): the cleaned `forIn` loop over the index list, generalized
over the accumulator, folds to `acc ++ featureNamesSpec`. -/
theorem featureNamesByNode_forIn (featureNames : List String) :
    ∀ (features : List Int) (acc : List (Option String)),
      Id.run (forIn features acc (fun i r =>
        (if i ≠ sentinelIndex then
            (pure (ForInStep.yield (r ++ [featureNames[i.toNat]?])) : Id _)
         else
            pure (ForInStep.yield (r ++ [none])))))
      = acc ++ featureNamesSpec featureNames features := by
  intro features
  induction features with
  | nil =>
    intro acc
    simp only [List.forIn_nil, featureNamesSpec, List.append_nil]; rfl
  | cons a as ih =>
    intro acc
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : a ≠ sentinelIndex
    · simp only [if_pos h, featureNamesSpec, featureNameAt, ih, List.append_assoc,
        List.cons_append, List.nil_append]
    · simp only [if_neg h, featureNamesSpec, featureNameAt, ih, List.append_assoc,
        List.cons_append, List.nil_append]

theorem correct_featureNamesByNode :
    ∀ (featureNames : List String) (features : List Int),
      problem_spec_featureNamesByNode featureNames features
        (implementation_featureNamesByNode featureNames features) := by
  intro featureNames features
  unfold problem_spec_featureNamesByNode implementation_featureNamesByNode
  -- bridge the desugared `do … for … mut …` body to the helper's clean body
  have h2 :
      (Id.run do
        let mut acc : List (Option String) := []
        for i in features do
          if i ≠ sentinelIndex then
            acc := acc ++ [featureNames[i.toNat]?]
          else
            acc := acc ++ [none]
        return acc)
      = Id.run (forIn features ([] : List (Option String)) (fun i r =>
          (if i ≠ sentinelIndex then
              (pure (ForInStep.yield (r ++ [featureNames[i.toNat]?])) : Id _)
           else
              pure (ForInStep.yield (r ++ [none]))))) := rfl
  rw [h2, featureNamesByNode_forIn]
  simp
-- proof-end
