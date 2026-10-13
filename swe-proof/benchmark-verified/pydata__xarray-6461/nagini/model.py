"""Twin-artifact model for pydata__xarray-6461.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When the conditional-selection routine is asked to preserve the attributes
  of its SECOND positional argument, the attribute mapping it preserves is the
  attribute mapping that BELONGS TO that second argument. If the second
  argument is a bare scalar (it carries no attribute mapping of its own), the
  preserved mapping is the empty mapping.

  The routine is also handed the list of attribute mappings of exactly those
  arguments that actually carry one, in argument order. That list is NOT a
  reliable positional handle on the second argument: a scalar argument
  contributes no entry, so the second argument's mapping need not sit at any
  constant offset in the list (and may be absent from it entirely). The preserved
  mapping must therefore be the second argument's OWN mapping, regardless of
  its position in that list (or its absence from it).

Attribute mappings are modelled as opaque integer identities (distinct
mappings have distinct identities; the empty mapping, which is also what a
scalar carries, is the identity 0). `present` is the list of identities of the
arguments that carry a mapping, in order. `x_attrs` is the identity of the
second argument's own mapping. `x_pos` locates the second argument's mapping
inside `present` (-1 when the second argument carries no mapping, i.e. it is a
scalar). The carried structural fact — an entry actually present in `present`
agrees with the owning argument's identity — is required so the result must be
the second argument's mapping as PRODUCED from that argument, not merely a
value read at a constant list offset.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No axiomatized callees: the changed operation is modelled deeply as the
#  selection of the second argument's own attribute identity.)
# axioms-end


# pure-start
# (No pure helpers needed.)
# pure-end


def attrs_to_keep(present: List[int], x_attrs: int, x_pos: int) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(present), 1 / 2))
    # `x_pos` locates the second argument's own mapping within `present`, or is
    # -1 when the second argument carries no mapping (it is a scalar).
    Requires(x_pos == -1 or (0 <= x_pos and x_pos < len(present)))
    # When the second argument's mapping is present in the list, the list entry
    # at that position is exactly the second argument's own mapping.
    Requires(Implies(0 <= x_pos and x_pos < len(present),
                     present[x_pos] == x_attrs))
    # A scalar second argument carries the empty mapping (identity 0).
    Requires(Implies(x_pos == -1, x_attrs == 0))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(present), 1 / 2))
    # The preserved mapping is the second argument's OWN mapping.
    Ensures(Result() == x_attrs)
    # post-conditions-end
    # impl-start
    return x_attrs
    # impl-end
