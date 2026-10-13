import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The unchanged persistence operation invoked repeatedly
   reports, for each invocation, the number of rows it matched — a non-negative
   integer. That value is carried into this model as a `Nat` element of
   `matched`; the only relied-upon property (a rows-matched value is
   non-negative) is encoded by the carrier type itself, so no separate `axiom`
   is needed. Its non-negativity is nonetheless validated against the real
   operation by axiom_check.py (G-AX), and the deep-model reference is recorded
   in mapping.md / meta.json. -/
-- axioms-end

-- pure-start
/- The total number of rows matched across a sequence of invocations: the
   running total of the individual rows-matched values. Front-recursive so a
   single unfold is available per loop step (the Velvet fold pattern, plan
   §5.4); an empty sequence totals to zero. -/
def totalMatched : List Nat → Nat
  | []      => 0
  | c :: cs => c + totalMatched cs

@[grind] lemma totalMatched_nil : totalMatched [] = 0 := rfl
@[grind] lemma totalMatched_cons (c : Nat) (cs : List Nat) :
    totalMatched (c :: cs) = c + totalMatched cs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method totalRowsMatched (matched : List Nat) return (out : Nat)
  ensures out = totalMatched matched
  do
    -- impl-start
    let mut result : Nat := 0
    let mut i := matched.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ matched.length
      invariant result = totalMatched (matched.drop i)
      done_with i = 0
      decreasing i
    do
      let c := matched[i - 1]!
      result := c + result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `totalMatched` peels one summand. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma totalMatched_drop_step (matched : List Nat) (i : Nat)
    (hi : 0 < i) (hle : i ≤ matched.length) :
    totalMatched (matched.drop (i - 1)) = matched[i - 1]! + totalMatched (matched.drop i) := by
  have hlt : i - 1 < matched.length := by omega
  have hcons : matched.drop (i - 1) = matched[i - 1]! :: matched.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, totalMatched_cons]

prove_correct totalRowsMatched by
  loom_solve
  rw [totalMatched_drop_step matched i (by omega) (by omega)]
  simp_all
