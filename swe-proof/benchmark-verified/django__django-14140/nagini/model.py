"""Twin-artifact model for django__django-14140.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A logical filter node is taken apart into a reconstruction triple
  ``(path, positional_arguments, keyword_arguments)`` so that an equivalent node
  can later be rebuilt by calling the same class with those arguments. This
  routine concerns the ``positional_arguments`` and ``keyword_arguments`` halves,
  computed from the node's three observable pieces of state: its ordered
  ``children`` (each an opaque sub-condition), its combining ``connector``, and
  whether it is ``negated``.

  The desired behaviour is uniform in the number of children:

    (1) Every child of the node, in order, is a positional argument; the
        positional arguments are exactly the node's children with nothing added,
        dropped, reordered, or relocated. In particular a node holding a single
        child still surfaces that one child positionally -- it is NOT special-
        cased into a keyword argument, so an opaque child that cannot be taken
        apart as a key/value pair is still reproduced faithfully.

    (2) The keyword arguments record only the two pieces of state that are not
        carried by the children themselves: a connector entry is present exactly
        when the node's connector differs from the class default, and a negation
        entry is present exactly when the node is negated. No child ever appears
        among the keyword arguments.

The node is modelled as a minimal class carrying only the touched state: the
``children`` (a ``List[int]`` of opaque child identifiers), the integer
``connector`` and ``default`` connector codes, and the ``negated`` flag. The
positional arguments are returned as a freshly built ``List[int]``; the presence
of each of the two possible keyword entries is returned as a boolean.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No unchanged opaque callee is consumed by the proof. The decomposition of a
#  node into its reconstruction arguments is the changed behaviour and is
#  modelled deeply below over the node's own state: the positional arguments are
#  the children verbatim, and the two keyword flags are exact boolean functions
#  of the connector/default relation and the negation flag. There is no
#  @ContractOnly axiom; equality of this deep model to the real method is the
#  refinement boundary documented in mapping.md, checked out-of-band by
#  axiom_check.py / G-AX, an A-reference, not a consumed axiom.)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


class Node:
    """A logical filter node, holding only the state ``deconstruct`` observes."""

    def __init__(self, children: List[int], connector: int, default: int,
                 negated: bool) -> None:
        Requires(Acc(list_pred(children), 1 / 2))
        Ensures(Acc(self.children) and self.children is children)  # type: ignore
        Ensures(Acc(self.connector) and self.connector == connector)  # type: ignore
        Ensures(Acc(self.default) and self.default == default)  # type: ignore
        Ensures(Acc(self.negated) and self.negated == negated)  # type: ignore
        Ensures(Acc(list_pred(children), 1 / 2))
        self.children = children
        self.connector = connector
        self.default = default
        self.negated = negated


class Deconstruction:
    """The argument halves of the reconstruction triple: the positional
    ``args`` (a freshly built list of the node's children) and the presence of
    each of the two possible keyword entries."""

    def __init__(self, args: List[int], connector_kwarg: bool,
                 negated_kwarg: bool) -> None:
        Requires(Acc(list_pred(args)))
        Ensures(Acc(self.args) and self.args is args)  # type: ignore
        Ensures(Acc(self.connector_kwarg) and self.connector_kwarg == connector_kwarg)  # type: ignore
        Ensures(Acc(self.negated_kwarg) and self.negated_kwarg == negated_kwarg)  # type: ignore
        Ensures(Acc(list_pred(args)))
        Ensures(ToSeq(self.args) == Old(ToSeq(args)))  # type: ignore  # content preserved
        self.args = args
        self.connector_kwarg = connector_kwarg
        self.negated_kwarg = negated_kwarg


def deconstruct_arguments(node: Node) -> Deconstruction:
    # pre-conditions-start
    Requires(Acc(node.children, 1 / 2))
    Requires(Acc(list_pred(node.children), 1 / 2))
    Requires(Acc(node.connector, 1 / 2))
    Requires(Acc(node.default, 1 / 2))
    Requires(Acc(node.negated, 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    # The node is read-only: its state is returned untouched at half permission.
    Ensures(Acc(node.children, 1 / 2))
    Ensures(Acc(list_pred(node.children), 1 / 2))
    Ensures(Acc(node.connector, 1 / 2))
    Ensures(Acc(node.default, 1 / 2))
    Ensures(Acc(node.negated, 1 / 2))
    # The result is a freshly built decomposition the caller fully owns.
    Ensures(Acc(Result().args))
    Ensures(Acc(list_pred(Result().args)))
    Ensures(Acc(Result().connector_kwarg))
    Ensures(Acc(Result().negated_kwarg))
    # (1) The positional arguments are exactly the node's children, in order,
    # for every node -- including a single-child node.
    Ensures(ToSeq(Result().args) == ToSeq(node.children))
    # (2) The connector keyword entry is present exactly when the connector
    # differs from the default; the negation entry exactly when negated; no
    # child is ever among the keyword arguments.
    Ensures(Result().connector_kwarg == (node.connector != node.default))
    Ensures(Result().negated_kwarg == node.negated)
    # post-conditions-end
    # impl-start
    # Every child becomes a positional argument (a faithful copy of the
    # children sequence), regardless of how many children there are.
    args = []  # type: List[int]
    i = 0
    n = len(node.children)
    while i < n:
        # invariants-start
        Invariant(Acc(node.children, 1 / 2))
        Invariant(Acc(list_pred(node.children), 1 / 2))
        Invariant(0 <= i and i <= n)
        Invariant(n == len(node.children))
        Invariant(Acc(list_pred(args)))
        Invariant(ToSeq(args) == ToSeq(node.children).take(i))
        # invariants-end
        Assert(ToSeq(node.children).take(i + 1) ==
               ToSeq(node.children).take(i) + PSeq(node.children[i]))
        args = args + [node.children[i]]
        i = i + 1
    Assert(i == n)
    Assert(n == len(ToSeq(node.children)))
    Assert(ToSeq(node.children).take(n) == ToSeq(node.children))
    Assert(ToSeq(args) == ToSeq(node.children))
    # The keyword arguments carry only the connector (when non-default) and the
    # negation flag; never a child.
    connector_kwarg = node.connector != node.default
    negated_kwarg = node.negated
    result = Deconstruction(args, connector_kwarg, negated_kwarg)
    Assert(ToSeq(result.args) == ToSeq(node.children))
    return result
    # impl-end
