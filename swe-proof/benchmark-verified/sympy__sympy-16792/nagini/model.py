"""Twin-artifact model for sympy__sympy-16792.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A code generator builds the ordered list of function arguments to match a
  caller-supplied argument sequence, then renders a C function prototype from
  it. Each requested argument falls into one of three kinds:

    * a plain scalar quantity;
    * a fixed-shape matrix quantity (always an array — its shape is intrinsic
      to the symbol);
    * an indexed-array quantity whose array shape is known only through the
      indexed entries that occur in the wrapped expression.

  Independently, each requested argument may or may not actually occur in the
  wrapped expression.

  The generated C prototype declares an argument as a pointer (`*name`) exactly
  when that argument is an array, and as a plain value (`name`) otherwise. The
  array-ness is resolved as follows, and element i of the rendered prototype is
  a pointer exactly when:

    * a matrix argument: ALWAYS — its shape is intrinsic, so it is an array
      whether or not it appears in the expression;
    * an indexed-array argument: only when it appears in the expression (its
      shape is recovered from the indexed entries that occur there);
    * a scalar argument: never.

  The behaviour the specification pins is that a matrix argument is declared as
  a pointer even when it does NOT appear in the wrapped expression — its
  intrinsic shape makes it an array regardless of use.

Each requested argument is modelled by a kind tag (`0` = scalar, `1` = matrix,
`2` = indexed-array) and a presence flag (does it occur in the expression). The
C prototype's per-argument pointer decision is rendered as a `bool`. The
specification is carried element-wise via the pure predicate `want_pointer`.

The array-ness decision and the prototype's pointer rendering are modelled
deeply (`shape_is_intrinsic`, `array_resolved`, `arg_is_pointer`); their
equality to the real shape/dimension computation and the real C prototype
renderer is checked out-of-band by axiom_check.py (G-AX), not consumed as an
axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no @ContractOnly axioms: the array-ness decision and the prototype's
# pointer rendering are modelled DEEPLY below as @Pure functions, and validated
# == the real sympy callees out-of-band by axiom_check.py / G-AX. There is no
# consumed axiom.)
# axioms-end


# pure-start
@Pure
def shape_is_intrinsic(k: int) -> bool:
    """Whether the argument's array shape is intrinsic to the symbol (a matrix,
    tag 1) rather than recovered from the expression (an indexed array, tag 2)
    or absent (a scalar, tag 0)."""
    return k == 1


@Pure
def array_resolved(k: int, present: bool) -> bool:
    """Whether the argument is resolved to be an array (and so carries a
    non-empty dimension list):
      * a matrix (intrinsic shape) is an array regardless of presence;
      * an indexed array is an array only when it appears in the expression;
      * a scalar is never an array."""
    if shape_is_intrinsic(k):
        return True
    if k == 2:
        return present
    return False


@Pure
def arg_is_pointer(has_dims: bool) -> bool:
    """The C prototype renders an argument as a pointer (`*name`) exactly when
    it carries a non-empty dimension list, and as a plain value otherwise."""
    return has_dims


@Pure
def want_pointer(k: int, present: bool) -> bool:
    """The desired pointer declaration for a requested argument of kind k that
    is/ is not present in the expression: a pointer iff the argument resolves
    to an array. A matrix is a pointer even when absent."""
    return arg_is_pointer(array_resolved(k, present))
# pure-end


def pointer_flags(kinds: List[int], present: List[bool]) -> List[bool]:
    # pre-conditions-start
    Requires(Acc(list_pred(kinds), 1 / 2))
    Requires(Acc(list_pred(present), 1 / 2))
    # the two parallel descriptors are aligned, one entry per requested argument
    Requires(len(kinds) == len(present))
    # each requested argument is scalar (0), matrix (1), or indexed array (2)
    Requires(Forall(int, lambda i: (Implies(0 <= i and i < len(kinds),
                                            0 <= kinds[i] and kinds[i] <= 2),
                                     [[kinds[i]]])))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(kinds), 1 / 2))
    Ensures(Acc(list_pred(present), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # the rendered prototype has exactly one flag per requested argument
    Ensures(len(Result()) == len(kinds))
    # each output flag is a pointer iff its argument resolves to an array; a
    # matrix argument is a pointer even when it is absent from the expression
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < len(kinds) and i < len(present),
                                           Result()[i] == want_pointer(kinds[i], present[i])),
                                    [[Result()[i]]])))
    # post-conditions-end
    # impl-start
    result = []  # type: List[bool]
    j = 0
    while j < len(kinds):
        # invariants-start
        Invariant(Acc(list_pred(kinds), 1 / 2))
        Invariant(Acc(list_pred(present), 1 / 2))
        Invariant(len(kinds) == len(present))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(kinds))
        Invariant(len(result) == j)
        Invariant(Forall(int, lambda i: (Implies(0 <= i and i < len(kinds),
                                                 0 <= kinds[i] and kinds[i] <= 2),
                                          [[kinds[i]]])))
        Invariant(Forall(int, lambda i: (Implies(0 <= i and i < j,
                                                 result[i] == want_pointer(kinds[i], present[i])),
                                          [[result[i]]])))
        Invariant(j <= len(present))
        Invariant(MustTerminate(len(kinds) - j + 1))
        # invariants-end
        k = kinds[j]
        is_present = present[j]
        # Resolve the argument's array-ness, then render the dimension flag.
        # A matrix is intrinsically an array and is given dimensions whether or
        # not it occurs in the expression. An indexed array is given dimensions
        # only when it occurs (its shape is recovered from the entries there).
        # A scalar never carries dimensions.
        if shape_is_intrinsic(k):
            has_dims = True
        elif k == 2:
            if is_present:
                has_dims = True
            else:
                has_dims = False
        else:
            has_dims = False
        flag = arg_is_pointer(has_dims)
        Assert(flag == want_pointer(k, is_present))
        old_result = result
        result = result + [flag]
        Assert(len(result) == j + 1)
        Assert(result[j] == want_pointer(kinds[j], present[j]))
        Assert(Forall(int, lambda i: (Implies(0 <= i and i < j,
                                              result[i] == old_result[i]),
                                       [[result[i]]])))
        j = j + 1
    return result
    # impl-end
