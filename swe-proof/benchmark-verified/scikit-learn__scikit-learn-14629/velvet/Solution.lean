import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- One per-target sub-model of a fitted multi-target classifier. Only the
   touched field is modeled: the collection of class labels that sub-model
   learned for its target. -/
structure Submodel where
  labels : List Int
  deriving Inhabited

/- The per-target class-label record of a fitted multi-target classifier: one
   label collection per sub-model, in sub-model order. Front-recursive so a
   single unfold is available per loop step (the fold pattern, plan §5.4). -/
def gatheredLabels : List Submodel → List (List Int)
  | []      => []
  | s :: ss => s.labels :: gatheredLabels ss

@[grind] lemma gatheredLabels_nil : gatheredLabels [] = [] := rfl
@[grind] lemma gatheredLabels_cons (s : Submodel) (ss : List Submodel) :
    gatheredLabels (s :: ss) = s.labels :: gatheredLabels ss := rfl

/- The record has exactly one entry per sub-model: its length equals the number
   of targets. (Mirrors the tested `len(...) == n_outputs`.) -/
@[grind] lemma gatheredLabels_length (ss : List Submodel) :
    (gatheredLabels ss).length = ss.length := by
  induction ss with
  | nil => rfl
  | cons s ss ih => simp [gatheredLabels, ih]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method gatherLabels (submodels : List Submodel) return (out : List (List Int))
  ensures out = gatheredLabels submodels
  ensures out.length = submodels.length
  do
    -- impl-start
    let mut result : List (List Int) := []
    let mut i := submodels.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ submodels.length
      invariant result = gatheredLabels (submodels.drop i)
      done_with i = 0
      decreasing i
    do
      let s := submodels[i - 1]!
      result := s.labels :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `gatheredLabels` peels one entry. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma gatheredLabels_drop_step (submodels : List Submodel) (i : Nat)
    (hi : 0 < i) (hle : i ≤ submodels.length) :
    gatheredLabels (submodels.drop (i - 1))
      = submodels[i - 1]!.labels :: gatheredLabels (submodels.drop i) := by
  have hlt : i - 1 < submodels.length := by omega
  have hcons : submodels.drop (i - 1) = submodels[i - 1]! :: submodels.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, gatheredLabels_cons]

prove_correct gatherLabels by
  loom_solve
  rw [gatheredLabels_drop_step submodels i (by omega) (by omega)]
  simp_all
