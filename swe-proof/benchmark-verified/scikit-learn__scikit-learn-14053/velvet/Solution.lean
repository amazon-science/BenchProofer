import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

/- Resolving a list of integer references against a table of names.

   We are given a table `names` and a list of integer references, one per item.
   Each reference is either a valid index into `names` (the item refers to that
   named entry) or a distinguished `sentinel` value meaning "this item refers to
   no entry at all". The task is to produce, for every item in order, its
   resolved label: the named entry when the reference is a real index, and "no
   label" (`none`) when the reference is the sentinel.

   The point of interest is the sentinel case: a sentinel reference must yield
   "no label" directly, WITHOUT being used as an index into `names` — the
   sentinel is not a valid position in the table and need not be one (the table
   may be shorter than any offset the sentinel might suggest). The model below
   computes the resolved labels abstractly; no callee is axiomatized because the
   per-reference resolution is the only computation. -/

-- axioms-start
-- (No axiomatized callees. The whole computation — per-reference resolution and
--  the assembly of the result list — is concrete list arithmetic over the two
--  inputs; there is no unchanged repo callee whose contract must be assumed.
--  See mapping.md §3 and refinement.md, all rows R or I.)
-- axioms-end

-- pure-start
/- A name, identified abstractly. Only the identity of a named entry is observed
   (which table slot it came from), never its concrete spelling, so a single
   opaque carrier suffices. -/
abbrev Name := Nat

/- Resolve a single integer reference against `names`. A sentinel reference
   resolves to `none` (no label) directly; any other reference `i` resolves to
   the named entry at position `i` (`names[i]?`). The sentinel branch never
   indexes into `names`. -/
def labelOne (names : List Name) (sentinel : Int) (i : Int) : Option Name :=
  if i = sentinel then none else names[i.toNat]?

/- Resolve a whole list of references: the per-reference resolution of each,
   in order. Front-recursive so a single unfold is available per loop step
   (the fold pattern, plan §5.4). -/
def labelsOf (names : List Name) (sentinel : Int) : List Int → List (Option Name)
  | []      => []
  | i :: is => labelOne names sentinel i :: labelsOf names sentinel is

@[grind] lemma labelsOf_nil (names : List Name) (sentinel : Int) :
    labelsOf names sentinel [] = [] := rfl
@[grind] lemma labelsOf_cons (names : List Name) (sentinel : Int)
    (i : Int) (is : List Int) :
    labelsOf names sentinel (i :: is)
      = labelOne names sentinel i :: labelsOf names sentinel is := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Resolve a list of integer references against a table of names.

   `names` is the table; `sentinel` is the distinguished value marking a
   reference to no entry; `refs` is the list of references (one per item).
   Every non-sentinel reference is required to be a valid index into `names`;
   sentinel references carry no such obligation — they resolve to "no label"
   without indexing, so the table may be shorter than the sentinel's magnitude.

   The result is `labelsOf`: for each reference in order, its named entry when
   the reference is a real index, and `none` when it is the sentinel.

   `names`, `sentinel`, `refs` are all read-only (none `mut`): the routine
   reads them and returns a result, mutating nothing it is handed (directive 5). -/
method buildLabels (names : List Name) (sentinel : Int) (refs : List Int)
    return (out : List (Option Name))
  require ∀ i ∈ refs, i ≠ sentinel → (0 ≤ i ∧ i.toNat < names.length)
  ensures out = labelsOf names sentinel refs
  do
    -- impl-start
    -- Walk the references back-to-front, prepending each resolved label.
    -- Resolution is per-reference: a sentinel reference becomes `none` directly
    -- (it is NOT used to index `names`); any other reference indexes the table.
    let mut result : List (Option Name) := []
    let mut idx := refs.length
    while idx > 0
      invariant 0 ≤ idx ∧ idx ≤ refs.length
      invariant result = labelsOf names sentinel (refs.drop idx)
      done_with idx = 0
      decreasing idx
    do
      let i := refs[idx - 1]!
      let lbl : Option Name := labelOne names sentinel i
      result := lbl :: result
      idx := idx - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer reference exposes the reference at
   `idx-1` on the front, so `labelsOf` peels one `labelOne`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma labelsOf_drop_step (names : List Name) (sentinel : Int)
    (refs : List Int) (idx : Nat)
    (hi : 0 < idx) (hle : idx ≤ refs.length) :
    labelsOf names sentinel (refs.drop (idx - 1))
      = labelOne names sentinel refs[idx - 1]!
        :: labelsOf names sentinel (refs.drop idx) := by
  have hlt : idx - 1 < refs.length := by omega
  have hcons : refs.drop (idx - 1) = refs[idx - 1]! :: refs.drop idx := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : idx - 1 + 1 = idx := by omega
    rw [h, hsucc]
  rw [hcons, labelsOf_cons]

prove_correct buildLabels by
  loom_solve
  rw [labelsOf_drop_step names sentinel refs idx (by omega) (by omega)]
  simp_all
