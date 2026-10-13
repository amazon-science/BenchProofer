"""Twin-artifact model for django__django-14672.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A reverse many-to-many relation derives an identity from which it computes a
  hash, so two relations that are equal by identity hash equally and a single
  relation can be placed in a hash-based container. One component carried in
  that identity is an optional, user-supplied collection of intermediate field
  names. That collection may be an ordinary mutable sequence (which is NOT
  hashable). For the identity to be usable as a hash key, EVERY component it
  carries must be hashable; therefore this component must be reduced to a
  hashable, order-preserving canonical form before it enters the identity:

    * an absent collection contributes an absent, hashable value unchanged;
    * a present sequence of names contributes the same names, in the same
      order, in an immutable (hashable) form.

  Two relations whose name collections are element-wise equal therefore yield
  equal canonical components (and hence equal identities and equal hashes).

A runtime value is modelled by a tagged carrier `Value` recording its kind
(absent / mutable-sequence / immutable-sequence) and its element sequence; a
mutable sequence is the only kind that is not hashable. Names are modelled as
`int` atoms and the name collection as `List[int]` (Nagini bans `str`
indexing); the element ordering is carried by the pure sequence theory
`PSeq[int]`.

The canonicalisation of one component is modelled deeply over `Value`; its
agreement with the real canonicaliser is checked out-of-band by axiom_check.py
(G-AX), not consumed as an axiom. Markers (machine-parsed) delimit the spec /
proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# axioms-end


# pure-start
# Carrier kinds. A mutable sequence (KIND_MUTABLE) is the only one that is not
# hashable; an absent value and an immutable sequence are both hashable.
KIND_ABSENT = 0    # None
KIND_MUTABLE = 1   # a Python list
KIND_IMMUTABLE = 2  # a Python tuple


class Value:
    """A minimal model of a runtime value as it enters the identity: a kind tag
    (faithfully reflecting the value's runtime type) plus its element sequence
    (empty when absent)."""

    def __init__(self, kind: int, items: PSeq[int]) -> None:
        Requires(0 <= kind and kind <= 2)
        # Loop-free constructor: two field stores, no call, no recursion. Level 2
        # so an obligated caller (level 6) has strict room above it and can hand
        # its unsatisfied obligation down (Nagini's leak check demands
        # caller-level > callee-level).
        Requires(MustTerminate(2))
        Ensures(Acc(self.kind) and self.kind == kind)
        Ensures(Acc(self.items) and self.items == items)
        self.kind = kind  # type: int
        self.items = items  # type: PSeq[int]


@Pure
def is_hashable(v: Value) -> bool:
    """Whether a value may participate in a hash. A mutable sequence is not
    hashable; an absent value and an immutable sequence are."""
    Requires(Acc(v.kind, 1 / 4))
    return v.kind != KIND_MUTABLE


@Pure
def canonical_names(names: Optional[List[int]]) -> int:
    """The KIND the name collection contributes to the identity after
    canonicalisation: absent stays absent; any present sequence becomes the
    immutable form."""
    Requires(Implies(names is not None, Acc(list_pred(names), 1 / 4)))
    if names is None:
        return KIND_ABSENT
    return KIND_IMMUTABLE


@Pure
def canonical_items(names: Optional[List[int]]) -> PSeq[int]:
    """The element sequence the name collection contributes after
    canonicalisation: order-preserving, identical to the input names (empty
    when absent)."""
    Requires(Implies(names is not None, Acc(list_pred(names), 1 / 4)))
    if names is None:
        return PSeq(0).take(0)
    return ToSeq(names)
# pure-end


def identity_name_component(names: Optional[List[int]]) -> Value:
    # pre-conditions-start
    # The name collection is read-only (directive 5): canonicalisation copies
    # it, it is not mutated.
    Requires(Implies(names is not None, Acc(list_pred(names), 1 / 2)))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Implies(names is not None, Acc(list_pred(names), 1 / 2)))
    Ensures(Acc(Result().kind) and Acc(Result().items))
    # The component that enters the identity must be hashable, so the identity
    # itself is hashable and the relation can be used as a hash key.
    Ensures(is_hashable(Result()))
    # It preserves the names, in order (absent stays absent): equal collections
    # produce equal components, hence equal identities and equal hashes.
    Ensures(Result().kind == canonical_names(names))
    Ensures(Result().items == canonical_items(names))
    # post-conditions-end
    # impl-start
    empty = []  # type: List[int]
    if names is None:
        return Value(KIND_ABSENT, ToSeq(empty))
    return Value(KIND_MUTABLE, ToSeq(names))
    # impl-end
