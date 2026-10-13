"""Twin-artifact model for django__django-11299.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A filter condition is a tree. Each node carries an ordered list of children;
  a child is either a LEAF (an atomic comparison that resolves to a single
  column reference) or a GROUP (a nested sub-condition with its own children).
  When the tree is compiled, a single boolean *plain-column* mode is chosen at
  the top: when it is set, every column reference produced anywhere in the tree
  must be the bare, table-name-free form (the form that is valid inside a check
  constraint); when it is clear, every reference is the fully-qualified form.

  Processing a node walks its children in order, turning each leaf into one
  column reference and processing each group's own children in turn. The desired
  guarantee is that the plain-column mode chosen at the top governs EVERY leaf at
  EVERY depth — a leaf nested two or more levels deep must use the same column
  form as a leaf that is a direct child of the root.

  The observable result is, in left-to-right traversal order, one boolean per
  leaf: True iff that leaf's column reference is the bare plain form. With the
  top-level mode set, every entry must be True regardless of nesting depth; a
  single nested leaf left in the qualified form is the defect this specification
  forbids.

The condition tree is modelled as a small recursive node structure (`QNode`)
in sibling/inner linked form: `kind` (0 = leaf, 1 = group), `inner` (the head
of a group's own child list) and `nxt` (the next sibling in the current child
list). The per-leaf result is a `List[bool]`, with the specification carried
over `PSeq[bool]`. `leaf_modes` is the deep model of the traversal;
`compile_children` is the verified recursive traversal.

No callee is axiomatized: the change is pure tree-traversal logic, modelled
deeply. Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No consumed axioms. The behaviour under specification — every leaf's column
# form is governed by the top plain-column mode at every nesting depth — is
# modelled DEEPLY by the pure `leaf_modes` fold below and the verified recursive
# `compile_children` impl, not behind a @ContractOnly. G-EQ audits the
# refinement to the real compiler.)
# axioms-end


# pure-start
class QNode:
    """One position in a filter-condition tree, in sibling/inner linked form.
    A node is the head of a child list: `nxt` is the next sibling in that list;
    `inner` (for a group) is the head of the group's own child list."""

    def __init__(self, kind: int, inner: 'Optional[QNode]',
                 nxt: 'Optional[QNode]') -> None:
        Requires(Implies(inner is not None, Acc(q_pred(inner))))
        Requires(Implies(nxt is not None, Acc(q_pred(nxt))))
        Ensures(Acc(q_pred(self)))
        Ensures(q_kind(self) == kind)
        self.kind = kind      # 0 = leaf, 1 = group
        self.inner = inner    # head of a group's child list (meaningful if group)
        self.nxt = nxt        # next sibling in the current child list
        Fold(q_pred(self))


@Predicate
def q_pred(n: QNode) -> bool:
    return (Acc(n.kind) and Acc(n.inner) and Acc(n.nxt) and
            Implies(n.inner is not None, q_pred(n.inner)) and
            Implies(n.nxt is not None, q_pred(n.nxt)))


@Pure
def q_kind(n: QNode) -> int:
    Requires(Acc(q_pred(n), 1 / 2))
    return Unfolding(Acc(q_pred(n), 1 / 2), n.kind)


@Pure
def empty_modes() -> PSeq[bool]:
    return PSeq(True).take(0)


@Pure
def leaf_modes(head: Optional[QNode], plain: bool) -> PSeq[bool]:
    """Per-leaf plain-column flags for the child list starting at `head`, in
    left-to-right traversal order, when the surrounding mode is `plain`.

    A leaf contributes one flag equal to the current mode; a group contributes
    the flags of its own children evaluated at the SAME mode, followed by the
    flags of the rest of the list."""
    Requires(Implies(head is not None, Acc(q_pred(head), 1 / 2)))
    if head is None:
        return empty_modes()
    if q_kind(head) == 0:                       # leaf: one flag at current mode
        return Unfolding(Acc(q_pred(head), 1 / 2),
                         PSeq(plain) + leaf_modes(head.nxt, plain))
    # group: its children at the SAME mode, then continue with the siblings.
    return Unfolding(Acc(q_pred(head), 1 / 2),
                     leaf_modes(head.inner, plain) + leaf_modes(head.nxt, plain))
# pure-end


def append_all(result: List[bool], src: List[bool]) -> None:
    # pre-conditions-start
    Requires(Acc(list_pred(result)))
    Requires(Acc(list_pred(src), 1 / 2))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(result)))
    Ensures(Acc(list_pred(src), 1 / 2))
    Ensures(ToSeq(result) == Old(ToSeq(result)) + ToSeq(src))
    # post-conditions-end
    # impl-start
    i = 0
    while i < len(src):
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(Acc(list_pred(src), 1 / 2))
        Invariant(0 <= i and i <= len(src))
        Invariant(ToSeq(result) == Old(ToSeq(result)) + ToSeq(src).take(i))
        Invariant(MustTerminate(len(src) - i + 1))
        # invariants-end
        result.append(src[i])
        i = i + 1
    Assert(ToSeq(src).take(len(src)) == ToSeq(src))
    # impl-end


def compile_children(head: Optional[QNode], plain: bool) -> List[bool]:
    # pre-conditions-start
    Requires(Implies(head is not None, Acc(q_pred(head), 1 / 2)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Implies(head is not None, Acc(q_pred(head), 1 / 2)))
    Ensures(Acc(list_pred(Result())))
    # The traversal yields exactly one flag per leaf, in order, every flag
    # governed by the top mode at every nesting depth.
    Ensures(ToSeq(Result()) == leaf_modes(head, plain))
    # post-conditions-end
    # impl-start
    result = []  # type: List[bool]
    if head is None:
        return result
    Unfold(Acc(q_pred(head), 1 / 2))
    if head.kind == 0:                          # leaf -> one column reference
        result.append(plain)
        rest = compile_children(head.nxt, plain)
        append_all(result, rest)
        Fold(Acc(q_pred(head), 1 / 2))
        return result
    # group -> descend with the SAME mode, then continue with siblings.
    sub = compile_children(head.inner, plain)
    tail = compile_children(head.nxt, plain)
    Fold(Acc(q_pred(head), 1 / 2))
    append_all(result, sub)
    append_all(result, tail)
    return result
    # impl-end
