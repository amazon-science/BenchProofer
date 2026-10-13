import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (none: this bundle has no axiomatized callees — the modeled operation is a
--  pure boolean/arithmetic reduction over already-evaluated operand truth
--  values; see mapping.md §3 and refinement.md §C.)
-- axioms-end

-- pure-start
/- The number of operands that hold for one row: the running tally of the
   per-operand 1/0 indicators. Front-recursive so a single unfold is available
   per loop step (the backward-fold pattern). -/
def trueCount : List Bool → Nat
  | []      => 0
  | c :: cs => (if c then 1 else 0) + trueCount cs

@[grind] lemma trueCount_nil : trueCount [] = 0 := rfl
@[grind] lemma trueCount_cons (c : Bool) (cs : List Bool) :
    trueCount (c :: cs) = (if c then 1 else 0) + trueCount cs := rfl

/- The chained exclusive-or of a row's operands: true exactly when an odd number
   of them hold. This is the value the combined predicate must compute. -/
def parityOdd (xs : List Bool) : Bool := decide (trueCount xs % 2 = 1)

/- At most as many operands hold as there are operands. -/
lemma trueCount_le_length : ∀ xs : List Bool, trueCount xs ≤ xs.length
  | []      => by simp [trueCount]
  | c :: cs => by
      have ih := trueCount_le_length cs
      simp only [trueCount, List.length_cons]
      split <;> omega

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `trueCount` peels one indicator. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma trueCount_drop_step (xs : List Bool) (i : Nat)
    (hi : 0 < i) (hle : i ≤ xs.length) :
    trueCount (xs.drop (i - 1)) =
      (if xs[i - 1]! then 1 else 0) + trueCount (xs.drop i) := by
  have hlt : i - 1 < xs.length := by omega
  have hcons : xs.drop (i - 1) = xs[i - 1]! :: xs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, trueCount_cons]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method oddParityReduce (children : List Bool) return (out : Bool)
  ensures out = parityOdd children
  do
    -- impl-start
    let mut count : Nat := 0
    let mut i := children.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ children.length
      invariant count = trueCount (children.drop i)
      done_with i = 0
      decreasing i
    do
      let c := children[i - 1]!
      count := (if c then 1 else 0) + count
      i := i - 1
    return (decide (0 < count)) &&
      decide ((if children.length > 2 then count % 2 else count) = 1)
    -- impl-end

prove_correct oddParityReduce by
  loom_solve
  · rw [trueCount_drop_step children i (by omega) (by omega)]
    rw [‹count = trueCount (children.drop i)›]
  · injection i_3 with hc _
    subst done_1
    simp only [List.drop_zero] at invariant_2
    rw [← hc, invariant_2]
    (unfold parityOdd;
     have hle := trueCount_le_length children;
     by_cases hlen : children.length > 2 <;>
       simp only [hlen, if_true, if_false] <;>
       first
         | (have hb : trueCount children = 0 ∨ trueCount children = 1 ∨
                trueCount children = 2 := by omega;
            rcases hb with h | h | h <;> rw [h] <;> decide)
         | (by_cases hpar : trueCount children % 2 = 1 <;>
              [ (have hpos : 0 < trueCount children := by omega;
                 simp [hpar, hpos]) ; simp [hpar] ]))
