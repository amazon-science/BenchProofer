import Mathlib
-- imports-end

/-!
Rendering the column references of a nested boolean filter expression.

A filter condition is a finite TREE. Each leaf names a single model field; each
interior node groups a list of sub-conditions (the children may themselves be
leaves or further interior nodes — nesting is arbitrary). When the tree is
lowered to its column references, every leaf is rendered as one of two column
forms:

  * a BARE column — just the field's column name; or
  * a TABLE-QUALIFIED column — the column name prefixed by its table.

Which form to use is a single boolean choice supplied once at the top of the
lowering. The contract is that this choice is GLOBAL: it applies uniformly to
every leaf of the tree, at every nesting depth. A leaf buried inside several
levels of grouping must be rendered in exactly the same form as a leaf sitting
at the top level. The grouping structure itself and each leaf's field are
carried through unchanged — only the per-leaf column form is decided here.

The salient point is uniformity: the rendering form must not silently differ
between shallow and deeply-nested leaves.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The only behavior the
-- lowering reads from a leaf is its field name, and the only decision it makes
-- is the column form dictated by the global boolean flag. That decision is a
-- total, deterministic function of (flag, field), so it is modeled directly as
-- the pure helper `buildLeaf` (a type refinement of the real per-leaf column
-- constructor) rather than axiomatized. Hence no `opaque`/`axiom` callee
-- contract is needed.
-- axioms-end

-- pure-start
/-- A boolean filter expression, restricted to the structure the lowering reads:
a `leaf` naming one field, or an interior `node` holding an ordered list of
children. -/
inductive QTree where
  | leaf (field : String)
  | node (children : List QTree)
  deriving Repr

/-- The lowered column-reference tree, mirroring the input shape. A `col` carries
the field's name and a boolean: `true` ⇒ bare column, `false` ⇒ table-qualified. -/
inductive ColTree where
  | col (field : String) (bare : Bool)
  | node (children : List ColTree)
  deriving Repr

/-- Render a single leaf to its column reference: the field is preserved and the
column form is exactly the global flag (`true` ⇒ bare, `false` ⇒ qualified). -/
def buildLeaf (bare : Bool) (field : String) : ColTree :=
  ColTree.col field bare

/- The canonical lowering: every leaf is rendered with the same global flag, at
every depth, and the grouping structure is preserved. Defined as a clean
structural fold over the input tree; this is the behavior the result is pinned to. -/
mutual
def expectedCol (bare : Bool) : QTree → ColTree
  | .leaf field => buildLeaf bare field
  | .node children => .node (expectedCols bare children)
def expectedCols (bare : Bool) : List QTree → List ColTree
  | [] => []
  | c :: cs => expectedCol bare c :: expectedCols bare cs
end
-- pure-end

-- post-conditions-start
/-- The lowered tree is fully pinned to the inputs: it equals the canonical
lowering of `q` under the global flag `bare`. This determines the grouping
structure, every leaf's field, and — uniformly at every depth — every leaf's
column form. No output component is left free. -/
def problem_spec_resolveColumns (bare : Bool) (q : QTree) (result : ColTree) : Prop :=
  result = expectedCol bare q
-- post-conditions-end

-- impl-start
/- Lower a filter expression to its column references. Walking each node's
children in order: a leaf child is rendered directly (its column form taken from
the global flag), and a node child is lowered recursively, THREADING the same
global flag down into the recursion so deeply-nested leaves share it. -/
mutual
def implementation_resolveColumns (bare : Bool) : QTree → ColTree
  | .leaf field => buildLeaf bare field
  | .node children => .node (resolveChildren bare children)
def resolveChildren (bare : Bool) : List QTree → List ColTree
  | [] => []
  | child :: rest =>
      let built :=
        match child with
        | .leaf field => buildLeaf bare field
        | .node _      => implementation_resolveColumns bare child
      built :: resolveChildren bare rest
end
-- impl-end

-- proof-start
mutual
theorem impl_eq_expected (bare : Bool) :
    ∀ (q : QTree), implementation_resolveColumns bare q = expectedCol bare q
  | .leaf field => rfl
  | .node children => by
      simp only [implementation_resolveColumns, expectedCol]
      rw [impls_eq_expecteds bare children]
theorem impls_eq_expecteds (bare : Bool) :
    ∀ (qs : List QTree), resolveChildren bare qs = expectedCols bare qs
  | [] => rfl
  | c :: cs => by
      simp only [resolveChildren, expectedCols]
      rw [impls_eq_expecteds bare cs]
      cases c with
      | leaf field => rfl
      | node ch => simp only [impl_eq_expected bare (.node ch)]
end

theorem correct_resolveColumns :
    ∀ (bare : Bool) (q : QTree),
      problem_spec_resolveColumns bare q
        (implementation_resolveColumns bare q) := by
  intro bare q
  unfold problem_spec_resolveColumns
  exact impl_eq_expected bare q
-- proof-end
