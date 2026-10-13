"""Twin-artifact model for matplotlib__matplotlib-26342.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A drawable collection of geometry carries a sequence of geometry items and a
  flag recording whether its cached rendering is out of date. Installing a new
  sequence of geometry onto such a collection must, once the call returns,

    (1) make the collection hand back EXACTLY the sequence object that was
        supplied — a subsequent query for the collection's geometry returns the
        very same object, by identity, so a caller that supplied a prepared
        sequence sees that prepared sequence (and only it) used afterwards; and

    (2) mark the collection's cached rendering as out of date, so the next draw
        recomputes from the freshly installed geometry.

  The supplied sequence is read-only to this operation: its element contents are
  not altered (the operation stores the reference, it does not rewrite items),
  and no element is added or removed.

The collection is modelled as a minimal object exposing only the two touched
fields: the held geometry sequence (an object reference) and the out-of-date
flag (a bool). The geometry sequence is modelled as a `List[int]` of opaque
per-item identity tokens; reference identity of the stored sequence is carried
by Nagini's `is`, and read-only-ness by fractional permission on the supplied
sequence. No callee is axiomatized: the behaviour is pure object/state logic,
modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No consumed axioms: installing a geometry sequence is pure object/state
# logic (store a reference, set a flag), modelled deeply. There is no external
# callee the operation depends on.
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


class GeometryCollection:
    def __init__(self) -> None:
        Ensures(Acc(self.items) and Acc(list_pred(self.items)))  # type: ignore
        Ensures(len(self.items) == 0)  # type: ignore
        Ensures(Acc(self.out_of_date) and self.out_of_date is False)  # type: ignore
        self.items = []  # type: List[int]
        self.out_of_date = False  # type: bool


def install_geometry(self: GeometryCollection, new_items: List[int]) -> None:
    # pre-conditions-start
    # The collection's two touched fields are genuinely mutated: full
    # permission to the held-sequence reference and to the out-of-date flag.
    Requires(Acc(self.items))
    Requires(Acc(self.out_of_date))
    # The supplied sequence is read-only: required at fractional permission so
    # the operation may not rewrite its element contents.
    Requires(Acc(list_pred(new_items), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.items))
    Ensures(Acc(self.out_of_date))
    # (1) the collection now holds EXACTLY the supplied sequence object: a query
    # for its geometry returns the very same object, by identity.
    Ensures(self.items is new_items)
    # (2) the cached rendering is marked out of date.
    Ensures(self.out_of_date is True)
    # The supplied sequence is returned read-only and untouched: same object,
    # same length, same element contents in order.
    Ensures(Acc(list_pred(new_items), 1 / 2))
    Ensures(len(new_items) == Old(len(new_items)))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(new_items),
                                           new_items[k] == Old(new_items[k])))))
    # post-conditions-end
    # impl-start
    # Pre-patch skeleton: this operation was unsupported on the base
    # collection and performed no installation — control never reached an
    # assignment of the held sequence or the out-of-date flag. Modelled
    # faithfully as a body that installs nothing, so the post-state still
    # carries the prior held sequence and flag. The spec's identity and
    # out-of-date guarantees are therefore violated (G-DIFF).
    pass
    # impl-end
