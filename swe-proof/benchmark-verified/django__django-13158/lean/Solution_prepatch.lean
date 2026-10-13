import Mathlib
-- imports-end

/-!
Forcing a query to return an empty result set.

A query is a tree: a top node together with the list of sub-queries whose results
are *combined* into the top node's result (as for a union of several queries).
Each sub-query is itself such a tree, so the combination can nest to any depth.
A query that has no sub-queries is a plain leaf.

Each node carries one observable fact: whether its own row-selection has been
forced to match nothing (its "self-empty" marker).

The operation modeled here turns a query into one that is guaranteed to return an
EMPTY result set. For that guarantee to hold, marking only the top node is not
enough: because a node's result is the combination of its sub-queries' results, a
node that combines other queries still returns every row those sub-queries return.
The empty-result guarantee therefore must hold of the WHOLE tree — the top node
AND every sub-query, recursively, must have its row-selection forced to match
nothing. The shape of the tree (how many sub-queries each node combines, nested)
is unchanged: the operation only flips the self-empty markers, it never adds or
drops sub-queries.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The single touched fact of
-- a node — that its own row-selection has been forced to match nothing — is
-- modeled deeply as the boolean field `selfEmpty`; the operation that sets it is
-- spelled out (`selfEmpty := true`), not axiomatized. The recursion into the
-- combined sub-queries is a self-call (`implementation_makeEmpty`), modeled
-- deeply, so it is not an axiom either. Hence no `opaque`/`axiom` callee contract
-- is required.
-- axioms-end

-- pure-start
/-- A query node restricted to its observable structure: whether its own
row-selection has been forced to match nothing (`selfEmpty`), and the list of
sub-queries whose results are combined into this node's result. A node with an
empty `combined` list is a plain leaf. -/
inductive Query where
  | mk (selfEmpty : Bool) (combined : List Query)

/-- This node's own self-empty marker. -/
def Query.selfEmpty : Query → Bool
  | .mk e _ => e

/-- The sub-queries combined into this node's result. -/
def Query.combined : Query → List Query
  | .mk _ c => c

/-- The bare tree shape: the nesting of combined sub-queries, with every
self-empty marker erased. Two queries have the same shape exactly when they
combine the same number of sub-queries at every level, nested identically. -/
inductive Shape where
  | node (children : List Shape)

/-- Erase the self-empty markers, keeping only the combination structure. -/
def toShape : Query → Shape
  | .mk _ combined => .node (combined.map toShape)

/-- The empty-result guarantee: this node's own row-selection is forced to match
nothing AND, recursively, so is every sub-query whose result is combined into it.
Only then does the whole query return no rows under any combination. -/
def YieldsNothing : Query → Prop
  | .mk e combined => e = true ∧ ∀ q ∈ combined, YieldsNothing q
decreasing_by all_goals (have h := List.sizeOf_lt_of_mem ‹_ ∈ _›; simp_all; omega)
-- pure-end

-- post-conditions-start
/-- The result of forcing a query to be empty is fully pinned to the input:

  * `YieldsNothing result` — the empty-result guarantee holds of the WHOLE tree
    (the top node and every combined sub-query, recursively), so the query returns
    no rows under any combination; and
  * `toShape result = toShape q` — the combination structure is preserved exactly
    (frame): the operation flips self-empty markers only, it neither adds nor drops
    any sub-query at any level.

No output component is left free: the markers are pinned by `YieldsNothing` and the
structure is pinned by the shape equality. -/
def problem_spec_makeEmpty (q : Query) (result : Query) : Prop :=
  YieldsNothing result ∧ toShape result = toShape q
-- post-conditions-end

-- impl-start
/-- Force a query to return an empty result set: mark this node's own
row-selection to match nothing. (Pre-fix skeleton: only the top node's marker is
flipped; the combined sub-queries are carried through untouched.) -/
def implementation_makeEmpty : Query → Query
  | .mk _ combined => Id.run do
    -- Force this node's own row-selection to match nothing.
    return Query.mk true combined
-- impl-end

-- proof-start
-- Gold proof body carried over verbatim; it fails to typecheck against the
-- pre-fix impl, because the combined sub-queries keep their stale markers and so
-- `YieldsNothing` cannot be discharged for them (G-DIFF).
theorem forIn_acc (combined : List Query) : ∀ (acc : List Query),
    (Id.run (forIn combined acc (fun sub r =>
      (pure (ForInStep.yield (r ++ [implementation_makeEmpty sub])) : Id _))))
      = acc ++ combined.map implementation_makeEmpty := by
  induction combined with
  | nil => intro acc; simp
  | cons a as ih =>
    intro acc; rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    rw [ih]; simp

theorem impl_eq (e : Bool) (combined : List Query) :
    implementation_makeEmpty (.mk e combined)
      = Query.mk true (combined.map implementation_makeEmpty) := by
  unfold implementation_makeEmpty
  have h := forIn_acc combined []
  simp only [Id.run, bind] at h ⊢
  rw [h]; rfl

theorem correct_makeEmpty : ∀ q : Query,
    problem_spec_makeEmpty q (implementation_makeEmpty q)
  | .mk e combined => by
    rw [impl_eq]
    constructor
    · unfold YieldsNothing
      refine ⟨rfl, ?_⟩
      intro x hx
      simp only [List.mem_map] at hx
      obtain ⟨a, ha, rfl⟩ := hx
      exact (correct_makeEmpty a).1
    · unfold toShape
      congr 1
      rw [List.map_map]
      apply List.map_congr_left
      intro a ha
      simp only [Function.comp_apply]
      exact (correct_makeEmpty a).2
decreasing_by all_goals (have h := List.sizeOf_lt_of_mem ‹_ ∈ _›; simp_all; omega)
-- proof-end
