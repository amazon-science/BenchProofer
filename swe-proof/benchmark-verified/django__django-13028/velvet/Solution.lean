import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No axioms. Every callee the modeled operation touches is an attribute read
-- or a structural traversal, modeled directly as a field of `Node` / as the
-- flattened node sequence (a type refinement, mapping.md §2); cross-language
-- soundness of those refinements is checked mechanically by G-CONF, so there
-- is no opaque callee to over-approximate here.
-- axioms-end

-- pure-start
/- One visited node of the operand tree. `filterable` is the node's own
   filterability flag (default-true elsewhere); `isOperand` records whether the
   node is a query operand — the kind of object whose filterability flag is
   meaningful — as opposed to a plain value supplied as a comparison target. -/
structure Node where
  filterable : Bool
  isOperand : Bool
  deriving Inhabited

/- A single node is offending exactly when it is a query operand AND declares
   itself non-filterable. A plain value (not an operand) never offends, even
   when it carries a false filterability flag. -/
def nodeBad (n : Node) : Bool := n.isOperand && !n.filterable

/- The whole traversal offends iff some visited node offends. Front-recursive
   so a single unfold is available per loop step (the fold pattern, plan §5.4). -/
def anyBad : List Node → Bool
  | []      => false
  | n :: ns => nodeBad n || anyBad ns

@[grind] lemma anyBad_nil : anyBad [] = false := rfl
@[grind] lemma anyBad_cons (n : Node) (ns : List Node) :
    anyBad (n :: ns) = (nodeBad n || anyBad ns) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method filterClauseRejected (nodes : List Node) return (raised : Bool)
  ensures raised = anyBad nodes
  do
    -- impl-start
    let mut result : Bool := false
    let mut i := nodes.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ nodes.length
      invariant result = anyBad (nodes.drop i)
      done_with i = 0
      decreasing i
    do
      let n := nodes[i - 1]!
      result := nodeBad n || result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the node at
   `i-1` on the front, so `anyBad` peels one `nodeBad`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma anyBad_drop_step (nodes : List Node) (i : Nat)
    (hi : 0 < i) (hle : i ≤ nodes.length) :
    anyBad (nodes.drop (i - 1)) = (nodeBad nodes[i - 1]! || anyBad (nodes.drop i)) := by
  have hlt : i - 1 < nodes.length := by omega
  have hcons : nodes.drop (i - 1) = nodes[i - 1]! :: nodes.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, anyBad_cons]

prove_correct filterClauseRejected by
  loom_solve
  rw [anyBad_drop_step nodes i (by omega) (by omega)]
  simp_all
