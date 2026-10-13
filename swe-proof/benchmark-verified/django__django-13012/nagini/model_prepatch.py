"""Twin-artifact model for django__django-13012.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A composite query node merely *wraps* another query node to attach extra
  context (an output type) to it, without otherwise altering it. When the set
  of columns this composite contributes to a grouping clause is requested, the
  composite must contribute EXACTLY the columns the node it wraps would itself
  contribute for the same grouping request — it forwards the request to the
  wrapped node and returns that node's own answer.

  Over the family of wrapped nodes this specification models — the
  non-aggregate, constant-or-column-like nodes the behaviour above is about —
  the wrapped node's own grouping-column answer follows a simple rule: a bare
  constant node contributes NO grouping columns (its answer is the empty list),
  whereas an ordinary column-like node contributes itself (its answer is the
  one-element list naming that node). The decisive correctness consequence,
  within this modelled family, is therefore: for a wrapped constant the
  composite contributes nothing, and for a wrapped column-like node the
  composite contributes the WRAPPED node — in neither case does it contribute
  the composite object itself.

  This two-case rule, and the independence of the answer from the grouping
  request below, are scoped to that modelled family; they are NOT claimed for
  every conceivable wrapped node. The composite's contract — forwarding the
  request to the wrapped node and returning that node's own answer — holds for
  ANY wrapped node regardless; the two-case rule is just the wrapped node's
  behaviour on the family this bundle models and tests.

  The grouping request (an optional alias) is threaded to the wrapped node
  unchanged; for the modelled family of nodes the answer does not depend on it.

Grouping-column lists are modelled as `List[int]` of node identities (each int
is the identity of one contributed node). A query node carries only the two
data the behaviour touches: its own identity, and — when it is a wrapper — the
identity and constant-ness of the node it wraps. The wrapped node's own
grouping-column rule, on the modelled family, is modelled DEEPLY as the verified
function `base_group_by_cols` (with its pure sequence value
`base_group_cols_seq`), whose equality to the real wrapped-node callees on that
family — and the universal forwarding behaviour of the composite — is checked
out-of-band by axiom_check.py (G-AX), not consumed as an axiom.

Termination (total correctness): both modelled operations are bounded
computations (a two-way case split, plus for the composite one call into the
wrapped node's own rule) that must actually ANSWER — deliver their
grouping-column list. Nagini is a partial-correctness verifier by default, so
without an explicit obligation a non-terminating implementation (e.g. bare
self-recursion before returning) satisfies every `Ensures` vacuously; the real
operations always complete. The obligation is carried as `MustTerminate` in
each precondition, with strictly decreasing measures so the composite may
invoke the wrapped node's rule but neither routine may re-invoke itself.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class WrappingNode:
    def __init__(self, inner_id: int, inner_is_constant: bool, node_id: int) -> None:
        Requires(inner_id != node_id)
        Ensures(Acc(self.inner_id, 1 / 2) and self.inner_id == inner_id)            # type: ignore
        Ensures(Acc(self.inner_is_constant, 1 / 2) and self.inner_is_constant == inner_is_constant)  # type: ignore
        Ensures(Acc(self.node_id, 1 / 2) and self.node_id == node_id)               # type: ignore
        Ensures(self.inner_id != self.node_id)                                       # type: ignore
        self.inner_id = inner_id
        self.inner_is_constant = inner_is_constant
        self.node_id = node_id


# axioms-start
# (no @ContractOnly axiom is consumed: the wrapped node's grouping-column rule
#  is modelled deeply as `base_group_by_cols` below and validated against the
#  real callees out-of-band by axiom_check.py / G-AX — an A-reference, not a
#  consumed axiom.)
# axioms-end


# pure-start
@Pure
def base_group_cols_seq(node_id: int, is_constant: bool) -> PSeq[int]:
    """The grouping columns a wrapped node contributes, as a pure sequence of
    node identities, over the modelled family of non-aggregate
    constant-or-column-like nodes. A bare-constant node contributes nothing (the
    empty sequence); a column-like node in that family contributes itself (the
    one-element sequence naming it). This is the deep model of the WRAPPED
    node's own grouping-column rule on that family (G-AX validates it == the
    real callees on the family; nodes outside it, e.g. alias-dependent ones, are
    out of scope and exercised separately by G-AX via the forwarding contract)."""
    if is_constant:
        return PSeq(0).take(0)
    return PSeq(node_id)
# pure-end


def base_group_by_cols(node_id: int, is_constant: bool, request: Optional[int]) -> List[int]:
    # pre-conditions-start
    # The wrapped node's rule is a bounded two-way case split that must answer
    # (measure 2: it may call only builtin steps, never itself).
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # The wrapped node's own grouping-column rule: empty for a constant,
    # otherwise the one-element list naming the node itself.
    Ensures(ToSeq(Result()) == base_group_cols_seq(node_id, is_constant))
    # post-conditions-end
    # impl-start
    if is_constant:
        empty = []  # type: List[int]
        return empty
    one = [node_id]  # type: List[int]
    return one
    # impl-end


def wrapper_group_by_cols(node: WrappingNode, request: Optional[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(node.inner_id, 1 / 2))
    Requires(Acc(node.inner_is_constant, 1 / 2))
    Requires(Acc(node.node_id, 1 / 2))
    Requires(node.inner_id != node.node_id)
    # The composite must actually answer the grouping request (measure 3:
    # strictly above the wrapped node's rule, so it may invoke that rule but
    # never re-invoke itself).
    Requires(MustTerminate(10))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(node.inner_id, 1 / 2))
    Ensures(Acc(node.inner_is_constant, 1 / 2))
    Ensures(Acc(node.node_id, 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The composite contributes EXACTLY the columns the WRAPPED node itself
    # contributes for the same grouping request: empty for a constant, otherwise
    # the wrapped node. In particular the result is never the composite itself
    # (its identity `node.node_id` differs from the wrapped node's).
    Ensures(ToSeq(Result()) == base_group_cols_seq(node.inner_id, node.inner_is_constant))
    # post-conditions-end
    # impl-start
    # PRE-PATCH BEHAVIOUR: the composite has no own grouping-column rule and
    # falls through to the generic non-aggregate default, contributing ITSELF
    # rather than forwarding to the wrapped node. This fails the postcondition
    # for BOTH a wrapped constant (required []) and a wrapped column-like node
    # (required [inner_id]), since node_id differs from the wrapped node.
    selfcols = [node.node_id]  # type: List[int]
    return selfcols
    # impl-end
