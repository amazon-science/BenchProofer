"""Twin-artifact model for pylint-dev__pylint-4604.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A dotted reference expression names an outer object via a chain of member
  accesses, e.g. ``foo.Bar`` or ``pkg.mod.Cls``. The base of such a chain is a
  plain identifier; every link above it is a member-access node whose child is
  the expression being accessed. To learn which top-level identifiers a
  reference expression DEPENDS ON, a traversal records:

    * a plain identifier node  -> that identifier's name;
    * a member-access node     -> whatever its accessed child depends on
                                  (i.e. it descends to the base of the chain);
    * any other node           -> whatever that node depends on in its own
                                  right (it has no member-access link to
                                  descend, so its own dependencies stand).

  In particular, a bare dotted reference such as ``foo.Bar`` depends on the
  base identifier ``foo``: the traversal must descend through the member-access
  link and record ``foo``. Recording is append-only onto an accumulator; nodes
  already present are kept, and the dependencies of the visited expression are
  appended in traversal order.

The annotation expression is modelled as a small recursive node structure
(`AnnNode`): `kind` (0 = identifier, 1 = member access, anything else = other),
`name` (the identifier code for an identifier node), `own` (the dependencies a
node of any other shape carries in its own right), and `expr` (the accessed
child for a member-access node). Names are Unicode-code-point-style integer
identifiers; the accumulator is a `List[int]` and the specification is carried
over `PSeq[int]`. `referenced_names` is the deep model of the dependency set of
one reference expression; `record_references` is the verified traversal that
appends it to the accumulator.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No consumed axioms. The traversal's changed behaviour — descending through a
# member-access link to the base identifier — is modelled DEEPLY by the pure
# `referenced_names` fold below and the verified `record_references` impl, not
# behind a @ContractOnly. The deep model is validated == the real callee
# (the AST node traversal) out-of-band by axiom_check.py / G-AX, as an
# A-reference; nothing here is consumed by the proof.)
# axioms-end


# pure-start
class AnnNode:
    """A reference-expression node: identifier, member access, or other."""

    def __init__(self, kind: int, name: int, own: PSeq[int],
                 expr: 'Optional[AnnNode]') -> None:
        Requires(Implies(expr is not None, Acc(node_pred(expr))))
        Requires(MustTerminate(1))
        Ensures(Acc(node_pred(self)))
        Ensures(node_kind(self) == kind)
        Ensures(node_name(self) == name)
        Ensures(node_own(self) == own)
        Ensures(node_child(self) is expr)
        Ensures(Implies(expr is None, node_depth(self) == 1))
        Ensures(Implies(expr is not None,
                        node_depth(self) == Old(node_depth(expr)) + 1))
        self.kind = kind     # 0 = identifier, 1 = member access, else = other
        self.name = name     # identifier code (meaningful when kind == 0)
        self.own = own       # the node's OWN dependencies (meaningful when the
                             # node is neither an identifier nor a member access)
        self.expr = expr     # accessed child (meaningful when kind == 1)
        Fold(node_pred(self))


@Predicate
def node_pred(n: AnnNode) -> bool:
    return (Acc(n.kind) and Acc(n.name) and Acc(n.own) and Acc(n.expr) and
            Implies(n.expr is not None, node_pred(n.expr)))


@Pure
def node_kind(n: AnnNode) -> int:
    Requires(Acc(node_pred(n), 1 / 2))
    return Unfolding(Acc(node_pred(n), 1 / 2), n.kind)


@Pure
def node_name(n: AnnNode) -> int:
    Requires(Acc(node_pred(n), 1 / 2))
    return Unfolding(Acc(node_pred(n), 1 / 2), n.name)


@Pure
def node_own(n: AnnNode) -> PSeq[int]:
    """The dependencies the node carries in its OWN right, without descending a
    member-access link: the identifiers a node that is neither a plain
    identifier nor a member access contributes on its own."""
    Requires(Acc(node_pred(n), 1 / 2))
    return Unfolding(Acc(node_pred(n), 1 / 2), n.own)


@Pure
def node_child(n: AnnNode) -> Optional[AnnNode]:
    Requires(Acc(node_pred(n), 1 / 2))
    return Unfolding(Acc(node_pred(n), 1 / 2), n.expr)


@Pure
def node_depth(n: AnnNode) -> int:
    """Height of the node's child chain (>= 1): the structural measure the
    traversal's termination obligation decreases on."""
    Requires(Acc(node_pred(n), 1 / 2))
    Ensures(Result() > 0)
    if node_child(n) is None:
        return 1
    return Unfolding(Acc(node_pred(n), 1 / 2), 1 + node_depth(n.expr))


@Pure
def referenced_names(n: AnnNode) -> PSeq[int]:
    """Top-level identifiers the reference expression `n` depends on.

    An identifier depends on itself; a member access depends on whatever its
    accessed child depends on (descend to the base of the dotted chain); any
    other node depends on what it carries in its own right."""
    Requires(Acc(node_pred(n), 1 / 2))
    if node_kind(n) == 0:                 # identifier
        return PSeq(node_name(n))
    if node_kind(n) == 1:                 # member access -> descend to base
        e = node_child(n)
        if e is None:
            return PSeq(0).take(0)
        return Unfolding(Acc(node_pred(n), 1 / 2), referenced_names(n.expr))
    return node_own(n)                    # other -> its own dependencies
# pure-end


def record_references(names: List[int], node: AnnNode) -> None:
    # pre-conditions-start
    Requires(Acc(list_pred(names)))
    Requires(Acc(node_pred(node), 1 / 2))
    # Total correctness: the traversal must TERMINATE, within a measure that
    # shrinks with the node's child-chain height (so each descent step must
    # make structural progress).
    Requires(MustTerminate(node_depth(node) + 1))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(names)))
    Ensures(Acc(node_pred(node), 1 / 2))
    # The accumulator gains exactly the dependencies of `node`, appended in
    # traversal order; prior contents are preserved unchanged.
    Ensures(ToSeq(names) == Old(ToSeq(names)) + referenced_names(node))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
