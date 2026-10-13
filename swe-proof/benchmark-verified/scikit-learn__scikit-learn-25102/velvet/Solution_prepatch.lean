import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms. The column-projection operation is modeled deeply
-- (`selectMasked` / `keptCol` below); the real container-level masked column
-- projection it abstracts is validated == this deep model by axiom_check.py
-- (G-AX, an A-reference — see refinement.md / mapping.md §3).
-- axioms-end

-- pure-start
/- The contribution of a single column to the projected result: a column kept
   by the mask contributes exactly its own element type (its first component),
   preserved as-is; a column the mask drops contributes nothing. Each column is
   a pair `(d, keep)` where `d` is the column's element type (its identity,
   mapping.md §2) and `keep` is its mask bit. -/
def keptCol (p : Int × Bool) : List Int :=
  if p.2 then [p.1] else []

/- Projection of a whole frame: concatenate the per-column contributions in
   input order, so the result is the ordered subsequence of element types of
   exactly the masked-in columns, each preserved as-is. Front-recursive so a
   single unfold is available per loop step (the fold pattern, plan §5.4). -/
def selectMasked : List (Int × Bool) → List Int
  | []      => []
  | p :: ps => keptCol p ++ selectMasked ps

@[grind] lemma selectMasked_nil : selectMasked [] = [] := rfl
@[grind] lemma selectMasked_cons (p : Int × Bool) (ps : List (Int × Bool)) :
    selectMasked (p :: ps) = keptCol p ++ selectMasked ps := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method projectColumns (cols : List (Int × Bool)) return (out : List Int)
  ensures out = selectMasked cols
  do
    -- impl-start
    -- Pre-image skeleton: the projection routes through a single homogeneous
    -- buffer, so every retained column is emitted with one common element type
    -- (the homogeneous default, encoded `0`) rather than its own type. The
    -- frozen spec requires each kept column's own type (`selectMasked`, via
    -- `keptCol p = [p.1]`), so prove_correct MUST fail.
    let mut result : List Int := []
    let mut i := cols.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ cols.length
      invariant result = selectMasked (cols.drop i)
      done_with i = 0
      decreasing i
    do
      let c := cols[i - 1]!
      let e : List Int := if c.2 then [0] else []
      result := e ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the column at
   `i-1` on the front, so `selectMasked` peels one `keptCol`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma selectMasked_drop_step (cols : List (Int × Bool)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ cols.length) :
    selectMasked (cols.drop (i - 1)) = keptCol cols[i - 1]! ++ selectMasked (cols.drop i) := by
  have hlt : i - 1 < cols.length := by omega
  have hcons : cols.drop (i - 1) = cols[i - 1]! :: cols.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, selectMasked_cons]

prove_correct projectColumns by
  loom_solve
  rw [selectMasked_drop_step cols i (by omega) (by omega)]
  simp_all
