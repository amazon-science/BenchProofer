import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callee: whether any schema work is emitted is decided
--  entirely by the table-identity comparison, modeled deeply below. The
--  dependent-relation rewrites are spelled out as a per-relation fold of opaque
--  operation codes, not an axiomatized callee whose contract the proof
--  consumes.)
-- axioms-end

-- pure-start
/- One schedule entry per dependent relation: the schema rewrite each dependent
   relation contributes when the rename proceeds. Front-recursive so a single
   unfold is available per loop step (the Velvet fold pattern). Each relation's
   rewrite group is one entry (a constant marker code, distinct from the
   main-table move's code): the spec pins one entry PER relation, in relation
   order. -/
def relationOps : List Int → List Int
  | []      => []
  | _ :: rs => (2 : Int) :: relationOps rs

@[grind] lemma relationOps_nil : relationOps [] = [] := rfl
@[grind] lemma relationOps_cons (r : Int) (rs : List Int) :
    relationOps (r :: rs) = (2 : Int) :: relationOps rs := rfl

/- The main-table move emitted first when the rename proceeds. -/
def mainMove : Int := 1
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A model-rename is applied to the database driven entirely by whether the
   stored table identifier actually changes. The operation is handed the stored
   table identifier the model used before the rename (`beforeTable`) and the one
   it uses after (`afterTable`), plus the collection of dependent relations
   (`relations`) — the foreign keys pointing at this model and the auto-created
   link tables for its many-to-many relations.

   (1) When the before- and after- identifiers are the SAME, the operation is
       observationally inert: it issues NO schema work at all — not the main
       table move, and crucially not the rewrites of the dependent relations.
       The emitted schedule of schema operations is EMPTY.

   (2) When the two identifiers DIFFER, the operation proceeds: it emits the
       main-table move FIRST, followed by one rewrite per dependent relation,
       in relation order. Under the per-relation marker abstraction (each
       relation's rewrite group is one schedule entry) the emitted schedule is
       exactly `mainMove :: relationOps relations`.

   Both branches are pinned exactly. Emitting nothing when the table identifier
   is unchanged is the noop requirement; on the proceeding branch the schedule
   must cover the main move AND every dependent relation — an operation that
   moves the main table but skips (some of) the dependent-relation rewrites
   does NOT satisfy this contract, nor does one that reorders the main move
   after the rewrites.

   The two table identifiers are modeled as `Int` (only their equality is
   observable to the schema layer). Each dependent relation is one element of a
   `List Int`. `relations` is read-only (not `mut`); the step never mutates it
   (directive 5). The emitted schedule is a `List Int` of operation codes. -/
method renameSchedule (beforeTable : Int) (afterTable : Int) (relations : List Int) return (out : List Int)
  ensures beforeTable = afterTable → out = []
  ensures beforeTable ≠ afterTable → out = mainMove :: relationOps relations
  do
    -- impl-start
    -- Don't proceed when the table identifier is not changed: inert ⇒ empty.
    if beforeTable = afterTable then
      return []
    else
      -- The rename proceeds: emit the main-table move, then one rewrite per
      -- dependent relation (built back-to-front so a single fold unfold is
      -- available per loop step).
      let mut result : List Int := []
      let mut i := relations.length
      while i > 0
        invariant 0 ≤ i ∧ i ≤ relations.length
        invariant result = relationOps (relations.drop i)
        done_with i = 0
        decreasing i
      do
        result := (2 : Int) :: result
        i := i - 1
      return mainMove :: result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes one more relation
   on the front, so `relationOps` peels one entry. The single goal `loom_solve`
   leaves for the loop body. -/
lemma relationOps_drop_step (relations : List Int) (i : Nat)
    (hi : 0 < i) (hle : i ≤ relations.length) :
    relationOps (relations.drop (i - 1)) = (2 : Int) :: relationOps (relations.drop i) := by
  have hlt : i - 1 < relations.length := by omega
  have hcons : relations.drop (i - 1) = relations[i - 1]! :: relations.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, relationOps_cons]

prove_correct renameSchedule by
  loom_solve
  rw [relationOps_drop_step relations i (by omega) (by omega)]
  simp_all
