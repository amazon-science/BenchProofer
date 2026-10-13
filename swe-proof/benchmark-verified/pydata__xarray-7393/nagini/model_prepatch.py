"""Twin-artifact model for pydata__xarray-7393.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Producing a dense array of values for a coordinate must not change its data
  type. The data type of the produced array is determined by two inputs only:

    * when the caller requests a specific element type, the produced array has
      exactly that requested element type;

    * when the caller requests no element type, the produced array has the
      coordinate's own declared element type.

  A third input -- the element-type code that an intermediate representation
  happens to report for the same values (`storage_type`) -- MUST NOT influence
  the data type of the result. In particular, when no element type is requested
  the result's data type equals the coordinate's declared element type, even if
  some intermediate representation would report a different element-type code
  for those same values.

  In both cases the element VALUES are exactly the input values, carried
  through unchanged; only the array's data-type label is governed by the rule
  above.

Element types are modelled as opaque integer codes (distinct types have
distinct codes); a requested element type is `Optional[int]` (absent ~ no
request). The input values are a read-only `List[int]` carried through to the
produced dense array; `declared` is the coordinate's own declared element-type
code, while `storage_type` is the element-type code an intermediate
representation may report for the same values (a non-influencing input). The
result is a freshly constructed dense array object owning its element-type code
and its values.

No callee is axiomatized: the array-construction step is a fresh object whose
element-type code is governed entirely by the declared/requested codes and
whose values are copied from the (read-only) input values -- modelled deeply.
Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


# axioms-start
# (No axiomatized callees: the element-type-resolution and array-construction
#  steps are modelled deeply over opaque type codes and the carried values.)
# axioms-end


# pure-start
@Pure
def effective_type(requested: Optional[int], declared: int) -> int:
    """The element-type code the produced array must carry: the requested type
    when one is given, otherwise the coordinate's declared type. Never the
    `storage_type` code reported by an intermediate representation."""
    if requested is None:
        return declared
    return requested
# pure-end


class DenseArray:
    """A freshly produced dense array: an element-type code plus values."""

    def __init__(self) -> None:
        Ensures(Acc(self.etype) and self.etype == 0)
        Ensures(Acc(self.values) and Acc(list_pred(self.values)) and
                len(self.values) == 0)
        self.etype = 0  # type: int
        self.values = []  # type: List[int]


def materialize_level(requested: Optional[int], declared: int,
                      storage_type: int, level_values: List[int]) -> DenseArray:
    # pre-conditions-start
    # The input values are read-only (the result copies them, never mutates
    # them): fractional permission (directive 5).
    Requires(Acc(list_pred(level_values), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(level_values), 1 / 2))
    # A freshly built dense array, fully owned.
    Ensures(Acc(Result().etype) and Acc(Result().values) and
            Acc(list_pred(Result().values)))
    # The element-type code is the requested type if given, else the
    # coordinate's declared type -- never the `storage_type` code.
    Ensures(Result().etype == effective_type(requested, declared))
    # Stated by case: with no requested type the result type is the declared
    # type; with a requested type the result type is exactly that requested type.
    Ensures(Implies(requested is None, Result().etype == declared))
    Ensures(Implies(requested is not None, Result().etype == requested))
    # The element values are exactly the input values, carried through
    # unchanged.
    Ensures(ToSeq(Result().values) == ToSeq(level_values))
    # post-conditions-end
    # impl-start
    # Pre-patch skeleton: the per-label values are returned as the underlying
    # storage produced them -- the requested element type is ignored and the
    # array carries the storage's (possibly wider) element-type code. When no
    # element type is requested this exposes the incidental promotion.
    res = DenseArray()
    res.etype = storage_type
    i = 0
    while i < len(level_values):
        # invariants-start
        Invariant(Acc(list_pred(level_values), 1 / 2))
        Invariant(Acc(res.etype) and Acc(res.values) and Acc(list_pred(res.values)))
        Invariant(res.etype == storage_type)
        Invariant(0 <= i and i <= len(level_values))
        Invariant(ToSeq(res.values) == ToSeq(level_values).take(i))
        # invariants-end
        res.values.append(level_values[i])
        i = i + 1
    Assert(ToSeq(level_values).take(len(level_values)) == ToSeq(level_values))
    return res
    # impl-end
