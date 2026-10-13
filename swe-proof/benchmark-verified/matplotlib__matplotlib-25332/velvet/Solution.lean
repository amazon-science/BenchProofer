import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms and no deep-model reference. Two independent behaviours are
-- modeled here, each a pure transform over a grouping registry's own observable
-- content: (1) the serialisable snapshot taken of the registry's reference table
-- before it is written out, and (2) the live table rebuilt from such a snapshot
-- when it is read back. Both are total functions of the registry's reference
-- table; there is no foreign callee whose contract the proof assumes and none
-- that is deep-modeled. See refinement.md §C / mapping.md §3 (no `axiom`, no
-- A-reference).
-- axioms-end

-- pure-start
/- A single reference held in the grouping registry's table. `target` is the
   identity of the object referred to; `weak` records whether this reference is
   a live (non-serialisable) weak reference or a plain (serialisable) strong one.
   The registry's live table holds only weak references; a snapshot of it holds
   only strong ones. -/
structure Ref where
  target : Int
  weak : Bool
deriving DecidableEq, Inhabited, Repr

/- Turn one reference into its strong (serialisable) form, keeping the object it
   refers to. This is the per-reference content of taking a snapshot. -/
def strongify (r : Ref) : Ref := { r with weak := false }

/- Turn one reference back into a live weak reference to the same object. This is
   the per-reference content of rebuilding the live table from a snapshot. -/
def weaken (r : Ref) : Ref := { r with weak := true }

/- One table row is a representative reference paired with the list of references
   grouped under it. Strongifying / weakening a row applies the per-reference
   transform to the representative and to every member of its group. -/
def strongifyEntry (e : Ref × List Ref) : Ref × List Ref :=
  (strongify e.1, e.2.map strongify)

def weakenEntry (e : Ref × List Ref) : Ref × List Ref :=
  (weaken e.1, e.2.map weaken)

/- The snapshot of a whole reference table: strongify every row. Front-recursive
   so a single unfold is available per loop step (the fold pattern, plan §5.4). -/
def strongifyMap : List (Ref × List Ref) → List (Ref × List Ref)
  | []      => []
  | e :: es => strongifyEntry e :: strongifyMap es

/- The live table rebuilt from a snapshot: weaken every row. Same front-recursive
   shape. -/
def weakenMap : List (Ref × List Ref) → List (Ref × List Ref)
  | []      => []
  | e :: es => weakenEntry e :: weakenMap es

@[grind] lemma strongifyMap_nil : strongifyMap [] = [] := rfl
@[grind] lemma strongifyMap_cons (e : Ref × List Ref) (es : List (Ref × List Ref)) :
    strongifyMap (e :: es) = strongifyEntry e :: strongifyMap es := rfl
@[grind] lemma weakenMap_nil : weakenMap [] = [] := rfl
@[grind] lemma weakenMap_cons (e : Ref × List Ref) (es : List (Ref × List Ref)) :
    weakenMap (e :: es) = weakenEntry e :: weakenMap es := rfl

/- Round-trip fact at the level of a single reference: weakening a strongified
   reference restores exactly a weak reference to the same object — the snapshot
   and the rebuild compose to the identity on what a live table observes. Marked
   `@[grind]` so `loom_solve` discharges the round-trip postcondition. -/
@[grind] lemma weaken_strongify (r : Ref) : weaken (strongify r) = weaken r := by
  simp [weaken, strongify]
-- pure-end

-- pre-conditions-start
-- (no module-level preconditions; the inputs are always supplied)
-- pre-conditions-end

-- post-conditions-start
-- (the postconditions are the inline `ensures` clauses on the methods below)
-- post-conditions-end

/- The serialisable snapshot of the grouping registry's reference table.

   Desired behaviour: the live table holds weak references, which a value
   serialiser (pickle) cannot write out. The snapshot taken just before writing
   must therefore replace every reference — both each row's representative and
   every member of its group — with a strong reference to the same object, so the
   result carries no live weak reference yet records the exact same grouping. The
   reference table `mapping` is a read-only input (not `mut`); it is never altered
   in place (directive 5) — the result is the snapshot. -/
method snapshot (mapping : List (Ref × List Ref)) return (out : List (Ref × List Ref))
  ensures out = strongifyMap mapping
  do
    -- impl-start
    let mut result : List (Ref × List Ref) := []
    let mut i := mapping.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ mapping.length
      invariant result = strongifyMap (mapping.drop i)
      done_with i = 0
      decreasing i
    do
      let e := mapping[i - 1]!
      result := strongifyEntry e :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step for the snapshot: dropping one fewer row exposes the
   row at `i-1` on the front, so `strongifyMap` peels one `strongifyEntry`. This
   is the single goal `loom_solve` leaves for the loop body. -/
lemma strongifyMap_drop_step (xs : List (Ref × List Ref)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ xs.length) :
    strongifyMap (xs.drop (i - 1)) = strongifyEntry xs[i - 1]! :: strongifyMap (xs.drop i) := by
  have hlt : i - 1 < xs.length := by omega
  have hcons : xs.drop (i - 1) = xs[i - 1]! :: xs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, strongifyMap_cons]

prove_correct snapshot by
  loom_solve
  rw [strongifyMap_drop_step mapping i (by omega) (by omega)]
  simp_all

/- The live grouping registry table rebuilt from a serialisable snapshot.

   Desired behaviour: when the registry is read back, every strong reference in
   the snapshot — each row's representative and every member of its group — must
   be turned back into a live weak reference to the same object, reconstructing
   the original grouping with live references. `state` is a read-only input (not
   `mut`); it is never altered in place (directive 5) — the result is the rebuilt
   live table. The round-trip postcondition records that weakening a snapshotted
   reference yields exactly a live reference to the same object (the snapshot is
   loss-free): rebuilding after snapshotting preserves what the live table
   observes. -/
method rebuild (state : List (Ref × List Ref)) return (out : List (Ref × List Ref))
  ensures out = weakenMap state
  ensures ∀ r : Ref, weaken (strongify r) = weaken r
  do
    -- impl-start
    let mut result : List (Ref × List Ref) := []
    let mut i := state.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ state.length
      invariant result = weakenMap (state.drop i)
      done_with i = 0
      decreasing i
    do
      let e := state[i - 1]!
      result := weakenEntry e :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step for the rebuild: same shape as the snapshot's. -/
lemma weakenMap_drop_step (xs : List (Ref × List Ref)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ xs.length) :
    weakenMap (xs.drop (i - 1)) = weakenEntry xs[i - 1]! :: weakenMap (xs.drop i) := by
  have hlt : i - 1 < xs.length := by omega
  have hcons : xs.drop (i - 1) = xs[i - 1]! :: xs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, weakenMap_cons]

prove_correct rebuild by
  loom_solve
  rw [weakenMap_drop_step state i (by omega) (by omega)]
  simp_all
