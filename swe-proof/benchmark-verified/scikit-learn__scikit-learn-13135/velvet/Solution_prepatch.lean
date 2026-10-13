import Velvet.Std
import Mathlib.Data.List.Sort
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms. The one operation this computation delegates to an
-- unchanged library routine — the ascending reordering of the cluster
-- representatives — is modeled DEEPLY as `asc` (an order-preserving total sort)
-- below, and validated against the real routine by axiom_check.py (G-AX) as a
-- deep-model reference, not consumed as an axiom. The cluster representatives
-- themselves are taken as a free input (produced upstream, unchanged here).
-- axioms-end

-- pure-start
/- Consecutive-pair midpoints of a sequence, front-recursive so a single unfold
   is available per loop step (the backward-fold pattern). For a sequence of `m`
   values this yields the `m-1` averages of adjacent entries. -/
def mids : List Rat → List Rat
  | []             => []
  | [_]            => []
  | a :: b :: rest => (a + b) / 2 :: mids (b :: rest)

@[grind] lemma mids_nil  : mids [] = [] := rfl
@[grind] lemma mids_one (a : Rat) : mids [a] = [] := rfl
@[grind] lemma mids_cons2 (a b : Rat) (rest : List Rat) :
    mids (a :: b :: rest) = (a + b) / 2 :: mids (b :: rest) := rfl

/- A sequence of fewer than two entries has no adjacent pair, hence no midpoint. -/
@[grind] lemma mids_short (xs : List Rat) (h : xs.length ≤ 1) : mids xs = [] := by
  match xs with
  | []          => rfl
  | [_]         => rfl
  | _ :: _ :: _ => simp at h

/- The ascending reordering of a finite multiset of representatives. Total,
   order-preserving; a deep model of the library reordering routine, validated
   == the real routine by axiom_check.py (G-AX). -/
def asc (xs : List Rat) : List Rat := xs.mergeSort (· ≤ ·)

/- The boundary sequence the computation produces: the lower endpoint, the
   adjacent-pair midpoints of the ascending representatives, then the upper
   endpoint. This is the structural quantity the postcondition pins. -/
def boundaries (centers : List Rat) (lo hi : Rat) : List Rat :=
  [lo] ++ mids (asc centers) ++ [hi]

/- Backward-fold step: dropping one fewer element from a given sequence `ys`
   exposes the pair `(ys[i-2], ys[i-1])` on the front, so `mids` peels one
   midpoint. This is the single goal `loom_solve` leaves for the loop body. -/
lemma mids_drop_step (ys : List Rat) (i : Nat)
    (h2 : 2 ≤ i) (hle : i ≤ ys.length) :
    mids (ys.drop (i - 2)) = (ys[i-2]! + ys[i-1]!) / 2 :: mids (ys.drop (i - 1)) := by
  have hlt1 : i - 2 < ys.length := by omega
  have hlt2 : i - 1 < ys.length := by omega
  have e1 : ys.drop (i - 2) = ys[i-2]! :: ys.drop (i - 1) := by
    have h := List.drop_eq_getElem_cons hlt1
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt1, Option.getD_some]
    have hs : i - 2 + 1 = i - 1 := by omega
    rw [h, hs]
  have e2 : ys.drop (i - 1) = ys[i-1]! :: ys.drop i := by
    have h := List.drop_eq_getElem_cons hlt2
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt2, Option.getD_some]
    have hs : i - 1 + 1 = i := by omega
    rw [h, hs]
  rw [e1, e2, mids_cons2]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method computeBoundaries (centers : List Rat) (lo : Rat) (hi : Rat) return (out : List Rat)
  ensures out = boundaries centers lo hi
  do
    -- impl-start
    -- Pre-image skeleton: pair adjacent representatives in their ORIGINAL order,
    -- WITHOUT the ascending reorder. The frozen spec requires `boundaries`, whose
    -- midpoints are taken over `asc centers`; on unordered representatives this
    -- diverges, so prove_correct MUST fail (G-DIFF).
    let ys := centers
    let mut result : List Rat := []
    let mut i := ys.length
    while i ≥ 2
      invariant i ≤ ys.length
      invariant result = mids (ys.drop (i - 1))
      done_with i ≤ 1
      decreasing i
    do
      let m := (ys[i - 2]! + ys[i - 1]!) / 2
      result := m :: result
      i := i - 1
    return lo :: (result ++ [hi])
    -- impl-end

prove_correct computeBoundaries by
  loom_solve
  · -- loop body: the backward fold peels one midpoint (over the UNSORTED list)
    have he : i - 1 - 1 = i - 2 := by omega
    rw [he, mids_drop_step centers i (by omega) (by omega)]
    simp_all
  · -- exit (i ≤ 1): result = mids centers, but the frozen spec demands
    -- mids (asc centers). These differ whenever the representatives are not
    -- already ascending — the discriminating clause the fix repairs. UNPROVABLE.
    have hi0 : i - 1 = 0 := by omega
    simp only [boundaries, hi0, List.drop_zero, List.singleton_append] at *
    simp_all
