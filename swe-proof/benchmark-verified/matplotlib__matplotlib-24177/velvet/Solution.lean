import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees and no `:|` callee stubs. The behaviour under spec is
--  a pure structural expansion: the input is a list of groups, each group
--  already given as its own list of points. How a single group's point list is
--  produced is the identical, unchanged upstream computation and is not modeled
--  here (refinement.md §B / mapping.md §3); it is reproduced verbatim by the
--  conformance bridge. The collected point list is a pure function of the input
--  list of groups, so there is no consumed axiom.)
-- axioms-end

-- pure-start
/- A single collected point. This model pins WHICH points are collected and in
   what order, not their coordinate values, so the point payload is kept
   abstract; the conformance bridge supplies the real coordinates. -/
opaque Vertex : Type

/- The points collected from a list of groups: the in-order concatenation of the
   per-group point lists, over EVERY group, with every group's points retained.
   Front-recursive so a single unfold is available per loop step (the fold
   pattern, plan §5.4). -/
def collectAll : List (List Vertex) → List Vertex
  | []      => []
  | s :: ss => s ++ collectAll ss

@[grind] lemma collectAll_nil : collectAll [] = [] := rfl
@[grind] lemma collectAll_cons (s : List Vertex) (ss : List (List Vertex)) :
    collectAll (s :: ss) = s ++ collectAll ss := rfl

/- The backward-fold step: dropping one fewer group exposes the group at
   index `i-1` on the front, so `collectAll` peels one group's point list. This
   is the single goal `loom_solve` leaves for the loop body. -/
lemma collectAll_drop_step (segs : List (List Vertex)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ segs.length) :
    collectAll (segs.drop (i - 1)) = segs[i - 1]! ++ collectAll (segs.drop i) := by
  have hlt : i - 1 < segs.length := by omega
  have hcons : segs.drop (i - 1) = segs[i - 1]! :: segs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, collectAll_cons]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Collect the points of a list of groups. `segs` is the input list of groups,
   each already given as its own list of points; it is read-only (not `mut`) —
   the operation reads it and returns a fresh list (directive 5).

   Desired behaviour: the collected list is the in-order concatenation of the
   point lists of ALL the groups, with no group's points dropped on the way.
   Every group must contribute every one of its points; the result therefore
   contains exactly the points of every group, in order. -/
method collectVertices (segs : List (List Vertex)) return (out : List Vertex)
  ensures out = collectAll segs
  do
    -- impl-start
    let mut result : List Vertex := []
    let mut i := segs.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ segs.length
      invariant result = collectAll (segs.drop i)
      done_with i = 0
      decreasing i
    do
      let s := segs[i - 1]!
      result := s ++ result
      i := i - 1
    return result
    -- impl-end

prove_correct collectVertices by
  loom_solve
  rw [collectAll_drop_step segs i (by omega) (by omega)]
  simp_all
