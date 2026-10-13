"""Twin-artifact model for matplotlib__matplotlib-24627.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A drawing container owns an ordered collection of member elements. Each member
  records two back-references to the owners it is currently parented under: a
  host reference and a canvas reference (each present as an owner, or absent).

  When the container is reset to its empty state, two things must hold once the
  reset returns:

    (1) the container's collection of members is empty, and

    (2) every element that had been a member is fully de-parented: both of its
        back-references are cleared to "absent". A member that is dropped from
        the container must observe the same de-parented state that an element
        removed individually already observes, so a former member is not left
        still claiming an owner it no longer belongs to.

  An element's two back-references are modelled as ``Optional[int]`` owner
  tokens (a present owner ~ a non-``None`` token; absent ~ ``None``); the test
  observes them only via "is an owner" vs. "is absent". The collection is a
  ``List`` of element objects; per-element field permission is carried by a
  guarded ``Forall`` over the collection indices.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class Element:
    def __init__(self, host: Optional[int], canvas: Optional[int]) -> None:
        Ensures(Acc(self.host) and self.host is host)        # type: ignore
        Ensures(Acc(self.canvas) and self.canvas is canvas)  # type: ignore
        self.host = host      # type: Optional[int]
        self.canvas = canvas  # type: Optional[int]


class Container:
    def __init__(self) -> None:
        Ensures(Acc(self.members) and Acc(list_pred(self.members)))  # type: ignore
        Ensures(len(self.members) == 0)                              # type: ignore
        self.members = []  # type: List[Element]


# axioms-start
# (no callee is axiomatized: the reset is a pure object-graph mutation; the
#  changed behaviour is modelled deeply, not behind a @ContractOnly contract)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


def reset_container(self: Container) -> None:
    # pre-conditions-start
    Requires(Acc(self.members) and Acc(list_pred(self.members)))
    # full permission to every current member's two back-references (mutated)
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(self.members),
             Acc(self.members[k].host) and Acc(self.members[k].canvas)),
             [[self.members[k]]])))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.members) and Acc(list_pred(self.members)))
    # (1) the container's collection is empty afterwards.
    Ensures(len(self.members) == 0)
    # the former members survive as objects (read-only fractional permission).
    Ensures(Acc(list_pred(Old(self.members)), 1 / 2))
    # (2) every former member is fully de-parented: both back-references absent.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(Old(self.members)),
            Acc(Old(self.members)[k].host, 1 / 2)
            and Acc(Old(self.members)[k].canvas, 1 / 2)
            and Old(self.members)[k].host is None
            and Old(self.members)[k].canvas is None),
            [[Old(self.members)[k]]])))
    # post-conditions-end
    # impl-start
    # Pre-patch behaviour: the container's collection is replaced by the empty
    # collection, but the former members are left as-is — their host and canvas
    # back-references still point at the owners they no longer belong to (the
    # bug). Postcondition (2) is therefore unprovable.
    self.members = []
    # impl-end
