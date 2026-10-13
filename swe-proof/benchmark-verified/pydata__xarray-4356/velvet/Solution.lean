import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms: the only modeled callee is the element-count product,
-- which is modeled deeply by `prodList` below (an A-reference validated against
-- the real array reduction by axiom_check.py / G-AX), not axiomatized.
-- axioms-end

-- pure-start
/- The number of elements collapsed into one output cell when a reduction runs
   over a collection of dimensions: the product of the per-dimension extents.
   Front-recursive (one unfold per loop step — the fold pattern, plan §5.4); the
   empty product is 1 (a reduction over no dimensions touches a single cell). -/
def prodList : List Nat → Nat
  | []      => 1
  | x :: xs => x * prodList xs

@[grind] lemma prodList_nil : prodList [] = 1 := rfl
@[grind] lemma prodList_cons (x : Nat) (xs : List Nat) :
    prodList (x :: xs) = x * prodList xs := rfl

/- The missing-decision for one output cell, as a function of which shape the
   output takes. When the output still has at least one dimension
   (`remainingDimCount ≥ 1`) each cell aggregates the product of the collapsed
   extents, and is missing exactly when the present count falls short of the
   requirement. When the whole input collapses to a single value
   (`remainingDimCount = 0`) the cell aggregates every element, and is reported
   missing only when the value's representation admits a missing marker
   (`fillAdmissible`) AND the present count falls short — for representations
   that cannot carry a missing marker the cell is never reported missing
   regardless of the requirement. -/
def cellMissing
    (remainingDimCount : Nat) (reducedSizes : List Nat) (totalSize : Nat)
    (missingCount : Nat) (requiredCount : Nat) (fillAdmissible : Bool) : Bool :=
  if remainingDimCount ≥ 1 then
    decide (prodList reducedSizes < missingCount + requiredCount)
  else
    fillAdmissible && decide (totalSize - missingCount < requiredCount)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide, for one cell of the output, whether its aggregate must be reported
   as missing — for a reduction that collapses a collection of dimensions, no
   matter how many. `reducedSizes` are the extents of the collapsed dimensions
   and `missingCount` of those collapsed elements were missing; the caller
   demands at least `requiredCount` present ones. `remainingDimCount` is how many
   dimensions the output keeps: when it is positive the output is a shaped
   collection whose per-cell aggregate spans the product of the collapsed
   extents; when it is zero the whole input has collapsed to a single value that
   spans `totalSize` elements, and that single value is only ever flagged missing
   when its representation admits a missing marker (`fillAdmissible`). The
   decision is produced for EVERY reduction, including one whose collapsed
   dimensions were named as a sequence (`axisWasSequence`): collapsing several
   dimensions is handled exactly like collapsing one, so the post-state pins
   `out` to a produced decision independently of that flag (never a rejection).
   There is NO precondition: the decision is pinned for EVERY `requiredCount`,
   including a requirement of zero (a present count — at most the collapsed
   element count — can then never fall short, so nothing real is flagged). -/
method reductionMissingDecision
    (reducedSizes : List Nat) (missingCount : Nat) (requiredCount : Nat)
    (remainingDimCount : Nat) (totalSize : Nat)
    (fillAdmissible : Bool) (axisWasSequence : Bool)
    return (out : Except Unit Bool)
  ensures out = Except.ok
    (cellMissing remainingDimCount reducedSizes totalSize missingCount
       requiredCount fillAdmissible)
  do
    -- impl-start
    -- Always produce a decision (never reject), regardless of whether the
    -- collapsed dimensions were named as a sequence: `axisWasSequence` is not
    -- consulted. When the output keeps a dimension, count the collapsed elements
    -- as the product of the reduced extents (a backward fold) and report missing
    -- iff the present count is short. When the output is a single collapsed
    -- value, report missing only when its representation admits a missing marker
    -- (`fillAdmissible`) and the present count is short.
    if remainingDimCount ≥ 1 then
      let mut total : Nat := 1
      let mut i := reducedSizes.length
      while i > 0
        invariant 0 ≤ i ∧ i ≤ reducedSizes.length
        invariant total = prodList (reducedSizes.drop i)
        done_with i = 0
        decreasing i
      do
        let s := reducedSizes[i - 1]!
        total := s * total
        i := i - 1
      return Except.ok (decide (total < missingCount + requiredCount))
    else
      return Except.ok (fillAdmissible && decide (totalSize - missingCount < requiredCount))
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `prodList` peels one factor. The single goal
   `loom_solve` leaves for the loop body. -/
lemma prodList_drop_step (xs : List Nat) (i : Nat)
    (hi : 0 < i) (hle : i ≤ xs.length) :
    prodList (xs.drop (i - 1)) = xs[i - 1]! * prodList (xs.drop i) := by
  have hlt : i - 1 < xs.length := by omega
  have hcons : xs.drop (i - 1) = xs[i - 1]! :: xs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, prodList_cons]

prove_correct reductionMissingDecision by
  loom_solve <;>
    first
      | (rw [prodList_drop_step reducedSizes i (by omega) (by omega)]; simp_all)
      | (simp only [cellMissing]; split <;> simp_all)
