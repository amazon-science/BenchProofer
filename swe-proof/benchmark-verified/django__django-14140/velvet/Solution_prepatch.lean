import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. Decomposing a logical filter node into a reconstructable
   form is modeled DEEPLY in the `pure` region (`deconstructed`): the positional
   children, the optional recorded combinator, and the optional recorded
   negation are all concrete data, validated against the real node by G-CONF.
   There is no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- A child held by a logical filter node. A child is one of:
   • a key/value condition pair (the shape produced from a keyword condition);
   • a nested filter node;
   • an embedded boolean expression — a value that is neither a pair nor a node
     (it cannot be read as a length-2 key/value pair).
   Only this three-way shape is observable to a consumer of the decomposition
   (mapping.md §2); the payloads are opaque carriers. -/
inductive Child where
  | pair (key : String) (val : Int)
  | node
  | expr
  deriving DecidableEq, Inhabited

/- The combinator joining a node's children. `conj` is the default; `disj` is
   the only non-default value. -/
inductive Connector where
  | conj
  | disj
  deriving DecidableEq, Inhabited

/- A decomposition outcome that is not a successful reconstructable form: it
   arises only when a lone child is required to be read as a key/value pair but
   cannot be (an embedded boolean expression has no such pair shape). -/
inductive DeconErr where
  | notPair
  deriving DecidableEq

/- The reconstructable decomposition of a node:
   • `args`   — the positional children, in order;
   • `pairKw` — a lone key/value condition recorded as a keyword instead of a
     positional child (absent in the desired behaviour — see `deconstructed`);
   • `connKw` — the recorded combinator, present only when it is non-default;
   • `negKw`  — whether the node's negation is recorded.
   `(args, connKw, negKw)` are exactly the components the reconstruction reads
   back; `pairKw` is part of the shared vocabulary so the form can express any
   decomposition (mapping.md §2). -/
structure Decon where
  args : List Child
  pairKw : Option (String × Int)
  connKw : Option Connector
  negKw : Bool
  deriving DecidableEq

/- Decompose a node into its reconstructable form. Desired behaviour: every
   child is placed positionally in `args`, uniformly — a node with a single
   child is treated no differently from one with several, so a lone embedded
   boolean expression is carried through positionally rather than forced into a
   key/value reading (which would have no pair shape). The combinator is recorded
   only when non-default; negation is recorded when present. Decomposition always
   succeeds. -/
def deconstructed (children : List Child) (connector : Connector) (negated : Bool) :
    Except DeconErr Decon :=
  Except.ok {
    args := children,
    pairKw := none,
    connKw := (if connector ≠ Connector.conj then some connector else none),
    negKw := negated
  }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decompose a logical filter node into a path-free reconstructable form of its
   children, combinator and negation. `children`, `connector`, `negated` are
   read-only (directive 5). -/
method deconstructNode (children : List Child) (connector : Connector) (negated : Bool)
    return (out : Except DeconErr Decon)
  ensures out = deconstructed children connector negated
  do
    -- impl-start
    -- Pre-image skeleton: a node with exactly one child that is NOT itself a
    -- nested node is special-cased — the lone child is read as a key/value pair
    -- and recorded as a keyword instead of positionally, and an embedded boolean
    -- expression (no pair shape) cannot be read this way. The frozen spec places
    -- every child positionally and always succeeds, so prove_correct MUST fail.
    let result : Except DeconErr Decon :=
      match children with
      | [c] =>
        match c with
        | .node =>
          Except.ok { args := children, pairKw := none,
                      connKw := (if connector ≠ Connector.conj then some connector else none),
                      negKw := negated }
        | .pair k v =>
          Except.ok { args := [], pairKw := some (k, v), connKw := none, negKw := negated }
        | .expr =>
          Except.error DeconErr.notPair
      | _ =>
        Except.ok { args := children, pairKw := none,
                    connKw := (if connector ≠ Connector.conj then some connector else none),
                    negKw := negated }
    return result
    -- impl-end

prove_correct deconstructNode by
  loom_solve <;> simp_all [deconstructed]
