import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The operation builds the result purely from the two
--  input matrices and the insertion position by positional rearrangement; it
--  calls no outside function whose behaviour the proof must assume. The grid
--  materialization that turns the per-cell rule into a matrix is modeled DEEPLY
--  as the row-wise construction below, not consumed as an axiom or A-reference.
--  See refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- One result row of the combined matrix. A block of new elements (`orow`) is
   placed at column position `pos`; the original row's elements keep their order
   and sit on either side of the block — the first `pos` of them before it and
   ALL the rest after it. Modeled per code point as `List Int` (mapping.md §2):
   the leading segment of length `pos`, then the inserted block, then the
   trailing segment (everything from `pos` onward). Crucially the trailing
   segment is the SUFFIX of the original row, so no original element is dropped or
   duplicated. -/
def spliceRow (srow orow : List Int) (pos : Nat) : List Int :=
  srow.take pos ++ orow ++ srow.drop pos

/- The whole combined matrix, row by row: pair each original row with the
   corresponding row of the inserted block and splice them at `pos`. Because the
   per-cell rule is independent of the row index, the matrix is exactly this
   row-wise splice (mapping.md §1). Front-recursive over both row lists so a
   single unfold is available per loop step (the backward-fold pattern). -/
def spliceCols (pos : Nat) : List (List Int) → List (List Int) → List (List Int)
  | [],      _       => []
  | _ :: _,  []      => []
  | s :: ss, o :: os => spliceRow s o pos :: spliceCols pos ss os

@[grind] lemma spliceCols_nil_left (pos : Nat) (os : List (List Int)) :
    spliceCols pos [] os = [] := rfl
@[grind] lemma spliceCols_cons_nil (pos : Nat) (s : List Int) (ss : List (List Int)) :
    spliceCols pos (s :: ss) [] = [] := rfl
@[grind] lemma spliceCols_cons_cons (pos : Nat)
    (s o : List Int) (ss os : List (List Int)) :
    spliceCols pos (s :: ss) (o :: os) = spliceRow s o pos :: spliceCols pos ss os := rfl

/- Generic drop/peel: dropping one fewer element exposes the element at `i-1` on
   the front. Used to peel one row off each input per loop step. -/
lemma drop_pred_cons {α : Type} [Inhabited α] (xs : List α) (i : Nat)
    (hi : 0 < i) (hlt : i - 1 < xs.length) :
    xs.drop (i - 1) = xs[i - 1]! :: xs.drop i := by
  have h := List.drop_eq_getElem_cons hlt
  rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
  have hsucc : i - 1 + 1 = i := by omega
  rw [h, hsucc]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Combine two matrices by inserting the columns of the second into the first at
   a given column position, producing a matrix whose rows are the originals with
   the new block spliced in. The two matrices have the same number of rows
   (`srows.length = orows.length`); the result keeps every original element in its
   original order, placing the inserted block at `pos` and ALL the original
   elements from `pos` onward immediately after it.

   Both inputs are read-only (neither declared `mut`): the routine reads the two
   row collections and assembles a fresh result (directive 5). The result is
   pinned exactly as the row-wise splice `spliceCols`. -/
method insertColumns (srows : List (List Int)) (orows : List (List Int)) (pos : Nat)
    return (out : List (List Int))
  require srows.length = orows.length
  ensures out = spliceCols pos srows orows
  do
    -- impl-start
    -- Pre-image skeleton: each result row places the inserted block at `pos`,
    -- but the trailing segment is taken as the row's PREFIX of length
    -- `srow.length - pos` instead of its suffix (`srow.drop pos`). This is the
    -- pre-patch positional arithmetic; the frozen spec requires `spliceCols`
    -- (suffix from `pos` onward), so prove_correct MUST fail.
    let mut result : List (List Int) := []
    let mut i := srows.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ srows.length
      invariant result = spliceCols pos (srows.drop i) (orows.drop i)
      done_with i = 0
      decreasing i
    do
      let s := srows[i - 1]!
      let o := orows[i - 1]!
      let buggyRow : List Int := s.take pos ++ o ++ s.take (s.length - pos)
      result := buggyRow :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step over both row lists: dropping one fewer row from each
   input exposes the rows at `i-1`, so `spliceCols` peels one spliced row. This
   is the single goal `loom_solve` leaves for the loop body. -/
lemma spliceCols_drop_step (pos : Nat) (srows orows : List (List Int)) (i : Nat)
    (hi : 0 < i) (hs : i - 1 < srows.length) (ho : i - 1 < orows.length) :
    spliceCols pos (srows.drop (i - 1)) (orows.drop (i - 1)) =
      spliceRow srows[i - 1]! orows[i - 1]! pos
        :: spliceCols pos (srows.drop i) (orows.drop i) := by
  rw [drop_pred_cons srows i hi hs, drop_pred_cons orows i hi ho, spliceCols_cons_cons]

prove_correct insertColumns by
  loom_solve
  rw [spliceCols_drop_step pos srows orows i (by omega) (by omega) (by omega)]
  simp_all
