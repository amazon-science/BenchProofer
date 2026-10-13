"""Twin-artifact model for sympy__sympy-24661.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a symbolic expression is parsed in a non-evaluating mode, a comparison
  between two operands must be preserved as the corresponding symbolic
  comparison object rather than being collapsed to a concrete truth value.

  Concretely, the parse step that rewrites a syntax node so that the operation
  stays symbolic receives a comparison node carrying one comparison operator
  and two operands. For each of the six comparison operators

      strict-less, less-or-equal, strict-greater, greater-or-equal,
      not-equal, equal

  the rewritten node is a *call* to the matching symbolic-comparison
  constructor, applied to the (independently rewritten) left and right
  operands, with the non-evaluating flag set. The operator-to-constructor
  correspondence is the prescribed bijection

      strict-less -> Lt,  less-or-equal -> Le,  strict-greater -> Gt,
      greater-or-equal -> Ge,  not-equal -> Ne,  equal -> Eq.

  A comparison whose operator is none of these six (e.g. membership or
  identity) is returned unchanged: it is NOT turned into a symbolic-comparison
  call.

The comparison syntax node and its rewritten form are modelled as small
classes carrying only the fields the rewrite touches (the operator code, the
constructor code, the non-evaluating flag, and the two operand nodes). The
operand nodes are opaque carriers; the rewrite recurses into them but their
internal structure is irrelevant to the property under specification.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *


# Operator codes for the comparison operators a comparison node may carry.
OP_LT = 0   # strict-less
OP_LE = 1   # less-or-equal
OP_GT = 2   # strict-greater
OP_GE = 3   # greater-or-equal
OP_NE = 4   # not-equal
OP_EQ = 5   # equal
# Any operator code >= 6 denotes a comparison operator outside the relational
# set (e.g. membership / identity), which must NOT be converted.

# Constructor codes for the produced symbolic-comparison call.
REL_LT = 100
REL_LE = 101
REL_GT = 102
REL_GE = 103
REL_NE = 104
REL_EQ = 105
REL_NONE = -1   # sentinel: no symbolic-comparison constructor (node unchanged)


class Expr:
    """An opaque operand expression node (rewrite recurses into it; its
    internal structure is irrelevant to the property under specification)."""

    def __init__(self) -> None:
        Ensures(Acc(self.tag) and self.tag == 0)  # type: ignore[name-defined]
        self.tag = 0  # type: int


class Compare:
    """A comparison syntax node: one comparison operator and two operands."""

    def __init__(self, op: int, left: Expr, right: Expr) -> None:
        Requires(Acc(left.tag, 1 / 2) and Acc(right.tag, 1 / 2))
        Ensures(Acc(self.op) and self.op == op)  # type: ignore[name-defined]
        Ensures(Acc(self.left) and self.left is left)  # type: ignore[name-defined]
        Ensures(Acc(self.right) and self.right is right)  # type: ignore[name-defined]
        Ensures(Acc(left.tag, 1 / 2) and Acc(right.tag, 1 / 2))
        self.op = op        # type: int
        self.left = left    # type: Expr
        self.right = right  # type: Expr


class Node:
    """The rewritten node. Either a symbolic-comparison call
    (is_call == True), carrying the constructor code, the non-evaluating flag,
    and the two (visited) operands; or the unchanged comparison node
    (is_call == False)."""

    def __init__(self, is_call: bool, rel_class: int, evaluate: bool,
                 left: Optional[Expr], right: Optional[Expr],
                 op: int) -> None:
        Ensures(Acc(self.is_call) and self.is_call == is_call)  # type: ignore[name-defined]
        Ensures(Acc(self.rel_class) and self.rel_class == rel_class)  # type: ignore[name-defined]
        Ensures(Acc(self.evaluate) and self.evaluate == evaluate)  # type: ignore[name-defined]
        Ensures(Acc(self.left) and self.left is left)  # type: ignore[name-defined]
        Ensures(Acc(self.right) and self.right is right)  # type: ignore[name-defined]
        Ensures(Acc(self.op) and self.op == op)  # type: ignore[name-defined]
        self.is_call = is_call      # type: bool
        self.rel_class = rel_class  # type: int
        self.evaluate = evaluate    # type: bool
        self.left = left            # type: Optional[Expr]
        self.right = right          # type: Optional[Expr]
        self.op = op                # type: int


# axioms-start
# (no axioms: the rewrite is a pure, fully-expressible AST transformation;
#  it calls no unchanged external callee.)
# axioms-end


# pure-start
@Pure
def is_relational(op: int) -> bool:
    """The operator codes that name a symbolic comparison constructor."""
    return op == OP_LT or op == OP_LE or op == OP_GT or \
        op == OP_GE or op == OP_NE or op == OP_EQ


@Pure
def rel_class_of(op: int) -> int:
    """The prescribed operator-to-constructor correspondence."""
    if op == OP_LT:
        return REL_LT
    if op == OP_LE:
        return REL_LE
    if op == OP_GT:
        return REL_GT
    if op == OP_GE:
        return REL_GE
    if op == OP_NE:
        return REL_NE
    if op == OP_EQ:
        return REL_EQ
    return REL_NONE
# pure-end


def rewrite_comparison(node: Compare) -> Node:
    # pre-conditions-start
    Requires(Acc(node.op, 1 / 2))
    Requires(Acc(node.left, 1 / 2) and Acc(node.right, 1 / 2))
    Requires(Acc(node.left.tag, 1 / 2) and Acc(node.right.tag, 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(node.op, 1 / 2))
    Ensures(Acc(node.left, 1 / 2) and Acc(node.right, 1 / 2))
    Ensures(Acc(node.left.tag, 1 / 2) and Acc(node.right.tag, 1 / 2))
    Ensures(Acc(Result().is_call) and Acc(Result().rel_class) and
            Acc(Result().evaluate) and Acc(Result().left) and
            Acc(Result().right) and Acc(Result().op))
    # A relational comparison is converted to a symbolic-comparison call ...
    Ensures(Result().is_call == is_relational(node.op))
    # ... whose constructor matches the operator under the prescribed bijection.
    Ensures(Result().rel_class == rel_class_of(node.op))
    # The non-evaluating flag is set: a produced symbolic-comparison call never
    # evaluates its operands.
    Ensures(Result().evaluate == False)
    # ... applied to the two visited operands, in original left/right order.
    # The operand pin is UNCONDITIONAL: a produced symbolic-comparison call
    # carries the two operands in source order, and an unchanged non-relational
    # comparison keeps its own operands (the real rewrite returns the node
    # itself, operands included). Leaving the operands free on either branch
    # would admit an implementation that drops or reorders them.
    Ensures(Result().left is node.left and Result().right is node.right)
    # The operator code is preserved UNCONDITIONALLY: an unchanged
    # non-relational comparison keeps its operator, and a produced call records
    # the operator it was built from. This pins every field of the result as a
    # function of the input, leaving no unconstrained channel.
    Ensures(Result().op == node.op)
    # post-conditions-end
    # impl-start
    # Pre-patch: there is no dedicated handling for a comparison node, so the
    # default traversal returns the comparison node unchanged. It is never
    # converted to a symbolic-comparison call (so it later collapses to a
    # concrete truth value).
    return Node(False, REL_NONE, False, node.left, node.right, node.op)
    # impl-end
