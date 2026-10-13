import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (none) The changed behaviour — selecting each column's effective display
-- format from the supplied per-column format strings — is modeled DEEPLY in the
-- pure region below (no consumed axiom). Its soundness against the real
-- column-format selection helper is validated by axiom_check.py (G-AX) as an
-- A-reference; see mapping.md §3.
-- axioms-end

-- pure-start
/- Look the supplied format string up by column name. The supplied formats are a
   name → format-string association; absence yields `none`. First match wins
   (the association has unique names). -/
def lookupFormat : List (String × String) → String → Option String
  | [],            _  => none
  | (k, v) :: rest, nm => if nm = k then some v else lookupFormat rest nm

/- The effective display format of one column `(name, current)` given the
   supplied formats: if a format was supplied for this column's name it OVERRIDES
   the column's current format; otherwise the column keeps its current format. -/
def effFmt (m : List (String × String)) (col : String × Option String) : Option String :=
  match lookupFormat m col.1 with
  | some f => some f
  | none   => col.2

/- The effective formats of a whole column sequence: the per-column override
   applied element-wise. Front-recursive so a single unfold is available per loop
   step (the backward-fold pattern). -/
def effFormats (m : List (String × String)) :
    List (String × Option String) → List (Option String)
  | []      => []
  | c :: cs => effFmt m c :: effFormats m cs

@[grind] lemma effFormats_nil (m : List (String × String)) :
    effFormats m [] = [] := rfl
@[grind] lemma effFormats_cons (m : List (String × String))
    (c : String × Option String) (cs : List (String × Option String)) :
    effFormats m (c :: cs) = effFmt m c :: effFormats m cs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method effectiveFormats (cols : List (String × Option String))
    (formats : List (String × String)) return (out : List (Option String))
  ensures out = effFormats formats cols
  do
    -- impl-start
    let mut result : List (Option String) := []
    let mut i := cols.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ cols.length
      invariant result = effFormats formats (cols.drop i)
      done_with i = 0
      decreasing i
    do
      let c := cols[i - 1]!
      result := effFmt formats c :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the column at
   `i-1` on the front, so `effFormats` peels one `effFmt`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma effFormats_drop_step (m : List (String × String))
    (cols : List (String × Option String)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ cols.length) :
    effFormats m (cols.drop (i - 1))
      = effFmt m cols[i - 1]! :: effFormats m (cols.drop i) := by
  have hlt : i - 1 < cols.length := by omega
  have hcons : cols.drop (i - 1) = cols[i - 1]! :: cols.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, effFormats_cons]

prove_correct effectiveFormats by
  loom_solve
  rw [effFormats_drop_step formats cols i (by omega) (by omega)]
  simp_all
