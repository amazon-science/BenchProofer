import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The per-column value transformation is modeled DEEPLY by
   `convertRow`/`convertRows` (pure region) and validated against the real
   callee by axiom_check.py (G-AX, an A-reference), so there is no opaque oracle
   the proof leans on. -/
-- axioms-end

-- pure-start
/- One row carries, per column, an integer value as produced by the data
   source. A per-column transformer is an arbitrary `Int → Int`; the transform
   chosen for a column is applied to that column's value, and any column without
   a transformer (the list runs short) passes its value through unchanged. This
   is the per-position application, front-recursive in lock-step on the
   transformer list and the row. -/
def convertRow : List (Int → Int) → List Int → List Int
  | _,        []      => []
  | [],       v :: vs => v :: vs
  | f :: fs,  v :: vs => f v :: convertRow fs vs

/- A whole result is the per-row application of the column transformers.
   Front-recursive on the row list (the transformers stay constant) so a single
   unfold is available per loop step (the backward-fold pattern). -/
def convertRows (convs : List (Int → Int)) : List (List Int) → List (List Int)
  | []        => []
  | row :: rs => convertRow convs row :: convertRows convs rs

@[grind] lemma convertRows_nil (convs : List (Int → Int)) :
    convertRows convs [] = [] := rfl
@[grind] lemma convertRows_cons (convs : List (Int → Int))
    (row : List Int) (rs : List (List Int)) :
    convertRows convs (row :: rs) = convertRow convs row :: convertRows convs rs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method transformedResultRows (rows : List (List Int)) (convs : List (Int → Int))
    return (out : List (List Int))
  ensures out = convertRows convs rows
  do
    -- impl-start
    -- Build the converted result by walking the source rows from the back and
    -- prepending each row's per-column transform; the accumulator is exactly
    -- the conversion of the as-yet-unconsumed tail.
    let mut result : List (List Int) := []
    let mut i := rows.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ rows.length
      invariant result = convertRows convs (rows.drop i)
      done_with i = 0
      decreasing i
    do
      let row := rows[i - 1]!
      result := convertRow convs row :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer row exposes the row at `i-1` on
   the front, so `convertRows` peels one `convertRow`. This is the single goal
   `loom_solve` leaves for the loop body. -/
lemma convertRows_drop_step (convs : List (Int → Int))
    (rows : List (List Int)) (i : Nat) (hi : 0 < i) (hle : i ≤ rows.length) :
    convertRows convs (rows.drop (i - 1))
      = convertRow convs rows[i - 1]! :: convertRows convs (rows.drop i) := by
  have hlt : i - 1 < rows.length := by omega
  have hcons : rows.drop (i - 1) = rows[i - 1]! :: rows.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, convertRows_cons]

prove_correct transformedResultRows by
  loom_solve
  rw [convertRows_drop_step convs rows i (by omega) (by omega)]
  simp_all
