"""Twin-artifact model for django__django-12050.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A lookup right-hand side may be an *iterable* of items (an ordered list, or
  an ordered tuple). When such an iterable is normalised for use in a query,
  two things must hold of the normalised result:

    (1) each item is normalised independently and INDEPENDENT-of-position: the
        i-th item of the result is the per-item normalisation of the i-th input
        item, and the result has exactly as many items as the input; and

    (2) the result is an iterable of the SAME concrete iterable type as the
        input. An ordered list normalises to an ordered list; an ordered tuple
        normalises to an ordered tuple. The concrete container type is carried
        through unchanged, because downstream consumers whose behaviour depends
        on the exact iterable type (e.g. value-equality against a stored value)
        observe it.

The iterable is modelled as a minimal object exposing only the two touched
aspects: a `kind` tag distinguishing the two concrete iterable types (0 for an
ordered list, 1 for an ordered tuple) and `items: List[int]` carrying the
ordered item identities. `List[int]`/`PSeq` sequence reasoning carries the
per-item specification; an item is observed only through its normalised
identity.

The unchanged per-item normalisation primitive is axiomatized (`normalise_item`):
it maps one item identity to its normalised identity and is independent of the
surrounding container. Markers (machine-parsed) delimit the spec / proof / impl
regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def normalise_item(item: int) -> int:
    """The unchanged per-item normalisation primitive applied to one item of
    the iterable. It depends only on the item itself, not on the container that
    holds it, so normalising an item yields the same identity whether the item
    sits in a list or a tuple. Provenance + executable soundness: mapping.md /
    axiom_check.py.
    """
    Ensures(True)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


class Iterable:
    def __init__(self, kind: int) -> None:
        Requires(kind == 0 or kind == 1)
        Ensures(Acc(self.kind) and self.kind == kind)  # type: ignore
        Ensures(Acc(self.items) and Acc(list_pred(self.items)))  # type: ignore
        Ensures(len(self.items) == 0)
        self.kind = kind  # type: int
        self.items = []  # type: List[int]


def resolve_iterable_value(value: Iterable) -> Iterable:
    # pre-conditions-start
    Requires(Acc(value.kind, 1 / 2))
    Requires(Acc(value.items, 1 / 2) and Acc(list_pred(value.items), 1 / 2))
    Requires(value.kind == 0 or value.kind == 1)
    # pre-conditions-end
    # post-conditions-start
    # the input is read-only (returned at the same fractional permission) ...
    Ensures(Acc(value.kind, 1 / 2))
    Ensures(Acc(value.items, 1 / 2) and Acc(list_pred(value.items), 1 / 2))
    # ... the result is a fresh, fully-owned iterable ...
    Ensures(Acc(Result().kind) and Acc(Result().items) and Acc(list_pred(Result().items)))
    # (2) of the SAME concrete iterable type as the input.
    Ensures(Result().kind == value.kind)
    # (1) with exactly as many items, each the per-item normalisation of the
    # corresponding input item, in order.
    Ensures(len(Result().items) == len(value.items))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(value.items),
                                           Result().items[k] == normalise_item(value.items[k])))))
    # post-conditions-end
    # impl-start
    out = Iterable(value.kind)
    i = 0
    while i < len(value.items):
        # invariants-start
        Invariant(Acc(value.kind, 1 / 2))
        Invariant(Acc(value.items, 1 / 2) and Acc(list_pred(value.items), 1 / 2))
        Invariant(Acc(out.kind) and out.kind == value.kind)
        Invariant(Acc(out.items) and Acc(list_pred(out.items)))
        Invariant(0 <= i and i <= len(value.items))
        Invariant(len(out.items) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                 out.items[k] == normalise_item(value.items[k])))))
        # invariants-end
        out.items.append(normalise_item(value.items[i]))
        i = i + 1
    return out
    # impl-end
