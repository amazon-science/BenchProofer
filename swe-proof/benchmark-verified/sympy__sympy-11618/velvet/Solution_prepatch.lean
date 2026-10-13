import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- Conform a coordinate vector to a target ambient dimension `n`: keep its first
   `n` entries and pad the rest of the way with zero coordinates. The origin of
   the ambient space is all-zeros, so a missing coordinate contributes as 0. -/
def alignTo (xs : List Int) (n : Nat) : List Int :=
  xs.take n ++ List.replicate (n - xs.length) 0

@[grind, simp] lemma alignTo_length (xs : List Int) (n : Nat) :
    (alignTo xs n).length = n := by
  simp [alignTo, List.length_take, List.length_replicate]; omega

/- The squared Euclidean distance between two equally-positioned coordinate
   vectors: the sum of the squares of the per-coordinate differences, taken
   coordinate by coordinate. Front-recursive so a single unfold is available per
   loop step (the backward-fold pattern). On unequal lengths the surplus tail is
   dropped; callers align first so both vectors share a length. -/
def sumSqZip : List Int → List Int → Int
  | a :: u, b :: v => (a - b) ^ 2 + sumSqZip u v
  | _, _ => 0

@[grind] lemma sumSqZip_cons (a b : Int) (u v : List Int) :
    sumSqZip (a :: u) (b :: v) = (a - b) ^ 2 + sumSqZip u v := rfl

@[grind, simp] lemma sumSqZip_nil_left (v : List Int) : sumSqZip [] v = 0 := rfl

@[grind, simp] lemma sumSqZip_nil_right (u : List Int) : sumSqZip u [] = 0 := by
  cases u <;> rfl

/- The ambient dimension the two vectors are compared in. When the two points
   are of the same kind their coordinate counts already agree (`min = max`);
   when they are of different kinds the comparison is carried out in the larger
   ambient space, so the shorter vector is treated as embedded at the origin in
   the extra dimensions. -/
def commonLen (sameKind : Bool) (s q : List Int) : Nat :=
  if sameKind then min s.length q.length else max s.length q.length

/- The squared Euclidean distance: align both coordinate vectors to the common
   ambient dimension (zero-padding the shorter), then sum the squared
   per-coordinate differences. No coordinate is silently discarded. -/
def distSq (sameKind : Bool) (s q : List Int) : Int :=
  sumSqZip (alignTo s (commonLen sameKind s q)) (alignTo q (commonLen sameKind s q))

/- The backward-fold step: for two equal-length vectors, dropping one fewer
   element exposes the coordinate at index `i-1` on the front of both, so
   `sumSqZip` peels one squared-difference term. This is the single goal
   `loom_solve` leaves for the loop body. -/
lemma sumSqZip_drop_step (A B : List Int) (i : Nat)
    (hA : i ≤ A.length) (hAB : A.length = B.length) (hi : 0 < i) :
    sumSqZip (A.drop (i - 1)) (B.drop (i - 1))
      = (A[i-1]! - B[i-1]!) ^ 2 + sumSqZip (A.drop i) (B.drop i) := by
  have hltA : i - 1 < A.length := by omega
  have hltB : i - 1 < B.length := by omega
  have hsucc : i - 1 + 1 = i := by omega
  have hcA : A.drop (i - 1) = A[i-1]! :: A.drop i := by
    have h := List.drop_eq_getElem_cons hltA
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hltA, Option.getD_some, h, hsucc]
  have hcB : B.drop (i - 1) = B[i-1]! :: B.drop i := by
    have h := List.drop_eq_getElem_cons hltB
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hltB, Option.getD_some, h, hsucc]
  rw [hcA, hcB, sumSqZip_cons]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method distanceSq (sameKind : Bool) (s : List Int) (q : List Int) return (out : Int)
  ensures out = distSq sameKind s q
  do
    -- impl-start
    -- Pre-image skeleton: the two coordinate vectors are summed by a plain
    -- co-iteration that stops at the shorter one (no alignment to the common
    -- ambient dimension). The frozen spec demands `distSq`, which aligns to the
    -- common length first, so `prove_correct` MUST fail when the vectors differ
    -- in length.
    let L := min s.length q.length
    let mut acc : Int := 0
    let mut i := L
    while i > 0
      invariant 0 ≤ i ∧ i ≤ L
      invariant acc = sumSqZip (s.drop i) (q.drop i)
      done_with i = 0
      decreasing i
    do
      acc := (s[i-1]! - q[i-1]!) ^ 2 + acc
      i := i - 1
    return acc
    -- impl-end

prove_correct distanceSq by
  loom_solve
  · rw [sumSqZip_drop_step s q i (by simp_all) (by simp_all) (by omega)]
    simp_all
  · simp only [distSq, commonLen]
    simp_all
