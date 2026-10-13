"""Twin-artifact model for sympy__sympy-12489.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A finite arrangement value is described by two observable attributes: the
  KIND of value it is (its runtime construction family — the plain family, or
  any specialised family derived from it) and its CONTENT (the array of points
  0..n-1 in their rearranged order).

  When such a value is produced by the family's own internal builder — the
  routine other operations funnel through to mint a fresh value from a finished
  array of points — the freshly-minted value must belong to the SAME family the
  builder was reached through, not to a single privileged family. Concretely:

    (1) The internal builder, invoked on a family identifier and a finished
        array, yields a value whose family identifier is exactly the one it was
        invoked with, and whose content is exactly that array. It does not
        collapse every result onto one privileged family.

    (2) A binary combination of two values, evaluated as a method of the
        left-hand value, produces its result through the left-hand value's own
        family, so the combination of two values of a specialised family is
        again a value of that specialised family (and its content is the
        combined array). The combination must reach the builder THROUGH the
        left operand's family, not through one privileged family reference.

A value is modelled as a minimal class carrying only the two touched
attributes: ``kind`` (the family identifier, an int; a distinguished base
family is 0, any other int is a derived family) and ``array`` (the array form
as a ``List[int]``). The array content of the combination is the unchanged
numeric product and is carried through directly; the property under
specification is the propagation of the family identifier.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class Arrangement:
    def __init__(self, kind: int, array: List[int]) -> None:
        Requires(Acc(list_pred(array), 1 / 2))
        Requires(MustTerminate(2))
        Ensures(Acc(self.kind) and self.kind == kind)        # type: ignore
        Ensures(Acc(self.array) and self.array is array)     # type: ignore
        Ensures(Acc(list_pred(array), 1 / 2))
        self.kind = kind
        self.array = array


# axioms-start
# (none) — the family-propagating construction is modelled deeply; no callee is
# axiomatized. The unchanged numeric product carried by the combination is an
# R-refinement (refinement.md), not a consumed axiom.
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


def make(kind: int, array: List[int]) -> Arrangement:
    """The family's internal builder: mint a fresh value from a family
    identifier and a finished array of points."""
    # pre-conditions-start
    Requires(Acc(list_pred(array), 1 / 2))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().kind) and Acc(Result().array))
    # (1) The minted value belongs to exactly the family the builder was reached
    # through, and carries exactly the supplied array — every family identifier
    # is honoured, not collapsed onto one privileged family.
    Ensures(Result().kind == kind)
    Ensures(Result().array is array)
    Ensures(Acc(list_pred(Result().array), 1 / 2))
    # post-conditions-end
    # impl-start
    result = Arrangement(kind, array)  # type: Arrangement
    return result
    # impl-end


def combine(self: Arrangement, other: Arrangement,
            product: List[int]) -> Arrangement:
    """Binary combination of two values as a method of ``self``: the combined
    content ``product`` is minted as a value of ``self``'s own family."""
    # pre-conditions-start
    Requires(Acc(self.kind, 1 / 2) and Acc(self.array, 1 / 2))
    Requires(Acc(other.kind, 1 / 2) and Acc(other.array, 1 / 2))
    Requires(Acc(list_pred(product), 1 / 2))
    Requires(MustTerminate(10))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.kind, 1 / 2) and Acc(self.array, 1 / 2))
    Ensures(Acc(other.kind, 1 / 2) and Acc(other.array, 1 / 2))
    Ensures(Acc(Result().kind) and Acc(Result().array))
    # (2) The combination is produced through the LEFT operand's family, so its
    # family identifier is exactly ``self``'s — a combination of two values of a
    # derived family is again a value of that derived family.
    Ensures(Result().kind == self.kind)
    # Its content is exactly the combined array (the unchanged numeric product).
    Ensures(Result().array is product)
    Ensures(Acc(list_pred(Result().array), 1 / 2))
    # post-conditions-end
    # impl-start
    result = make(self.kind, product)  # type: Arrangement
    return result
    # impl-end
