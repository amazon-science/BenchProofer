import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- The total of one position: the sum of the values contributed there by every
   additive part of the expression. -/
def rowSum (r : List Rat) : Rat := r.foldr (· + ·) 0

/- The value the iterated multiplication must produce over a finite range: the
   running product, across all index positions, of each position's total. Each
   element of `M` is the list of part-values at one index position; the result
   is the genuine product of those positional totals. Front-recursive so a
   single unfold is available per loop step (the fold pattern, plan §5.4). -/
def prodOfSums : List (List Rat) → Rat
  | []      => 1
  | r :: rs => rowSum r * prodOfSums rs

@[grind] lemma prodOfSums_nil : prodOfSums [] = 1 := rfl
@[grind] lemma prodOfSums_cons (r : List Rat) (rs : List (List Rat)) :
    prodOfSums (r :: rs) = rowSum r * prodOfSums rs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- `M` carries, for each index position of the finite range, the list of the
   `width` additive part-values contributed at that position. The result is the
   product over positions of each position's total `rowSum`. A position whose
   total is 0 is outside the modeled domain: over such a range the repository's
   symbolic result is an undefined value with no rational image, so no `Rat`
   output is claimed there. -/
method productOverRange (M : List (List Rat)) (width : Nat) return (out : Rat)
  require ∀ r ∈ M, r.length = width
  require ∀ r ∈ M, rowSum r ≠ 0
  ensures out = prodOfSums M
  do
    -- impl-start
    let mut acc : Rat := 1
    let mut i := M.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ M.length
      invariant acc = prodOfSums (M.drop i)
      done_with i = 0
      decreasing i
    do
      let r := M[i - 1]!
      acc := rowSum r * acc
      i := i - 1
    return acc
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the position at
   `i-1` on the front, so `prodOfSums` peels one positional total. This is the
   single goal `loom_solve` leaves for the loop body. -/
lemma prodOfSums_drop_step (M : List (List Rat)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ M.length) :
    prodOfSums (M.drop (i - 1)) = rowSum M[i - 1]! * prodOfSums (M.drop i) := by
  have hlt : i - 1 < M.length := by omega
  have hcons : M.drop (i - 1) = M[i - 1]! :: M.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, prodOfSums_cons]

prove_correct productOverRange by
  loom_solve
  rw [prodOfSums_drop_step M i (by omega) (by omega)]
  simp_all
