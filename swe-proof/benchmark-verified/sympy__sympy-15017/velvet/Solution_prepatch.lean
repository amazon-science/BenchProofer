import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

/- The element count of a multi-dimensional array.

   A multi-dimensional array is described by a list of dimension sizes (its
   shape). The total number of elements it holds is the product of those
   dimension sizes. When the shape is empty — the array is a single scalar
   value — the product ranges over no factors, so it is the empty product,
   one: the array still holds exactly one element.

   The model below computes that product abstractly with a single fold; no
   callee is axiomatized because the fold is the only computation. -/

-- axioms-start
-- axioms-end

-- pure-start
/- The product of a sequence of dimension sizes, defined front-recursively so a
   single unfold is available per loop step (the Velvet fold pattern, plan
   §5.4). The empty sequence folds to the multiplicative identity, one. -/
def prodSeq : List Nat → Nat
  | []      => 1
  | d :: ds => d * prodSeq ds

@[grind] lemma prodSeq_nil : prodSeq [] = 1 := rfl
@[grind] lemma prodSeq_cons (d : Nat) (ds : List Nat) :
    prodSeq (d :: ds) = d * prodSeq ds := rfl
-- pure-end

-- pre-conditions-start
-- (one block per modeled method; this bundle models one method)
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The number of elements held by an array of the given shape: the product of
   its dimension sizes, with the empty shape (a scalar) yielding one. `dims`
   is the list of dimension sizes; it is read-only (not `mut`). -/
method arrayLength (dims : List Nat) return (n : Nat)
  ensures n = prodSeq dims
  do
    -- impl-start
    -- PREPATCH (buggy): when there are no dimensions the running total is left
    -- at zero instead of the multiplicative identity, so a scalar shape yields
    -- zero rather than one. The frozen spec requires `prodSeq dims` (empty
    -- product = 1), so prove_correct MUST fail.
    let mut result : Nat := if dims.length > 0 then 1 else 0
    let mut i := dims.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ dims.length
      invariant result = prodSeq (dims.drop i)
      done_with i = 0
      decreasing i
    do
      let d := dims[i - 1]!
      result := d * result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the dimension at
   `i-1` on the front, so `prodSeq` peels one factor. This is the single goal
   `loom_solve` leaves for the loop body. -/
lemma prodSeq_drop_step (dims : List Nat) (i : Nat)
    (hi : 0 < i) (hle : i ≤ dims.length) :
    prodSeq (dims.drop (i - 1)) = dims[i - 1]! * prodSeq (dims.drop i) := by
  have hlt : i - 1 < dims.length := by omega
  have hcons : dims.drop (i - 1) = dims[i - 1]! :: dims.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, prodSeq_cons]

prove_correct arrayLength by
  loom_solve
  rw [prodSeq_drop_step dims i (by omega) (by omega)]
  simp_all
