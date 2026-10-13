import Velvet.Std
-- imports-end

set_option maxHeartbeats 1000000
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axiom. The only operation under specification — assembling the
--  full report from the per-item entry sequences of a chain of related items —
--  is modeled DEEPLY below as `flattenSeq`. Each item's own entry sequence is
--  produced by an UNCHANGED sub-computation, so it is taken as the input
--  carrier `groups`, not axiomatized; the assembly's fidelity to the real
--  callee is validated out-of-band by conformance_check.py / G-CONF.)
-- axioms-end

-- pure-start
/- The complete report for a chain of related items: the entries contributed by
   the first item, followed by the entries contributed by each subsequent item,
   and nothing else. Each item's own entry sequence is an element of the input;
   an item that contributes no entries appears as an empty element and is simply
   skipped over without ending the assembly. Front-recursive (one unfold per
   item) so a backward impl loop that prepends one item's entries each step can
   discharge the value equality (the Velvet fold pattern, plan §5.4). -/
def flattenSeq : List (List Int) → List Int
  | []      => []
  | g :: gs => g ++ flattenSeq gs

@[grind] lemma flattenSeq_nil : flattenSeq [] = [] := rfl
@[grind] lemma flattenSeq_cons (g : List Int) (gs : List (List Int)) :
    flattenSeq (g :: gs) = g ++ flattenSeq gs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assemble the full report for a chain of related items. `groups` is the
   ordered sequence of per-item entry sequences (each already produced by the
   unchanged per-item traversal); the result is their in-order concatenation —
   every item contributes all of its entries, in order, regardless of whether
   any earlier item contributed none. `groups` is read-only (the traversal does
   not alter the per-item sequences). -/
method assembleReport (groups : List (List Int)) return (out : List Int)
  ensures out = flattenSeq groups
  do
    -- impl-start
    -- Build the report by folding the per-item entry sequences from the back,
    -- prepending each item's entries before the entries already gathered. The
    -- result is exactly the in-order concatenation of every item's entries.
    let mut result : List Int := []
    let mut i := groups.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ groups.length
      invariant result = flattenSeq (groups.drop i)
      done_with i = 0
      decreasing i
    do
      let g := groups[i - 1]!
      result := g ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `flattenSeq` peels one item's entries off the front of
   its output. This is the single goal `loom_solve` leaves for the loop body. -/
lemma flattenSeq_drop_step (groups : List (List Int)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ groups.length) :
    flattenSeq (groups.drop (i - 1)) = groups[i - 1]! ++ flattenSeq (groups.drop i) := by
  have hlt : i - 1 < groups.length := by omega
  have hcons : groups.drop (i - 1) = groups[i - 1]! :: groups.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, flattenSeq_cons]

prove_correct assembleReport by
  loom_solve
  rw [flattenSeq_drop_step groups i (by omega) (by omega)]
  simp_all
