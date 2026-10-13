import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee is invoked by the modeled behavior: `deconstruct` derives
-- its `(args, kwargs)` result purely from the node's stored components
-- (the child sequence, the combinator, and the negation flag) using only
-- language primitives (tuple/dict construction), which are modeled directly.
-- Hence there is no `opaque` callee and no consumed `_prop` axiom.
-- axioms-end

-- pure-start
/-- The logical combinator of a filter node. `cAnd` is the default. -/
inductive Connector where
  | cAnd
  | cOr
deriving DecidableEq, Inhabited, Repr

/-- A single child stored in a filter node. A node's children are either
key/value lookup pairs (index-addressable as `child[0]`/`child[1]`), standalone
conditional expressions (which carry a single value and are NOT index-addressable),
or nested filter nodes. `label` is an opaque tag for the latter two — the
decomposition never inspects their internal content. -/
inductive Child where
  | cond (key val : String)
  | expr (label : String)
  | nested (label : String)
deriving DecidableEq, Inhabited, Repr

/-- Whether a child is itself a nested filter node (`isinstance(child, Q)`). -/
def Child.isNode : Child → Bool
  | .nested _ => true
  | _ => false

/-- Index-addressing a child as a length-2 pair (`child[0]`, `child[1]`).
Defined only for key/value lookup children; `none` for the others (a standalone
expression child has no subscript, the source of the read failure when a single
such child is subscripted unconditionally). -/
def Child.asPair : Child → Option (String × String)
  | .cond k v => some (k, v)
  | _ => none

/-- The keyword-argument mapping returned by the decomposition. It can carry an
inlined key/value entry (the `pair`), the non-default combinator (`connector`),
and the negation flag (`negated`). -/
structure Kwargs where
  pair : Option (String × String)
  connector : Option Connector
  negated : Bool
deriving DecidableEq, Repr

/-- The decomposition triple of a filter node: an import path, the positional
arguments, and the keyword arguments. -/
structure Deconstructed where
  path : String
  args : List Child
  kwargs : Kwargs
deriving Repr
-- pure-end

-- post-conditions-start
/-- The decomposition of a filter node. The `path` is carried through unchanged.
Every child of the node is placed positionally into `args`, in order. The keyword
arguments carry no inlined key/value entry; they record the combinator only when
it is non-default, and the negation flag only when the node is negated.

This pins the result component-wise to the node's stored inputs (frame
discipline): `args` is exactly the child sequence, `kwargs.connector` is present
iff the combinator differs from the default, `kwargs.negated` mirrors the flag,
and `kwargs.pair` is always absent. -/
def problem_spec_deconstruct
    (path : String) (children : List Child)
    (connector : Connector) (negated : Bool)
    (result : Deconstructed) : Prop :=
  result.path = path ∧
  result.args = children ∧
  result.kwargs.pair = none ∧
  result.kwargs.connector = (if connector = Connector.cAnd then none else some connector) ∧
  result.kwargs.negated = negated
-- post-conditions-end

-- impl-start
def implementation_deconstruct
    (path : String) (children : List Child)
    (connector : Connector) (negated : Bool) : Deconstructed := Id.run do
  let mut args : List Child := []
  let mut kw : Kwargs := { pair := none, connector := none, negated := false }
  if children.length = 1 ∧ ¬ (children.headI.isNode) then
    let child := children.headI
    kw := { kw with pair := some (child.asPair.getD ("", "")) }
  else
    args := children
    if connector ≠ Connector.cAnd then
      kw := { kw with connector := some connector }
  if negated then
    kw := { kw with negated := true }
  return { path := path, args := args, kwargs := kw }
-- impl-end

-- proof-start
theorem correct_deconstruct :
    ∀ (path : String) (children : List Child)
      (connector : Connector) (negated : Bool),
      problem_spec_deconstruct path children connector negated
        (implementation_deconstruct path children connector negated) := by
  sorry   -- carries the gold proof intent; UNCLOSABLE against the pre-patch impl (G-DIFF)
-- proof-end
