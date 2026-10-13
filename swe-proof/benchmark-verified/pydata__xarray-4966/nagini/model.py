"""Twin-artifact model for pydata__xarray-4966.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A fixed-width integer array carries a stored signedness (its element values
  are either the unsigned or the signed view of a bit pattern of a known width)
  together with a requested target signedness supplied out of band. The decode
  operation reconciles the two: when the stored signedness disagrees with the
  request, every element is reinterpreted as the OTHER view of the same bit
  pattern of that width; otherwise the elements pass through unchanged. The two
  cases that disagree are symmetric:

    * a SIGNED-stored array whose request is "treat as unsigned" -> each element
      is mapped to its unsigned view (a negative value v becomes v + 2**bits);
    * an UNSIGNED-stored array whose request is "treat as signed" -> each element
      is mapped to its signed view (a value v at or above the half-range
      2**(bits-1) becomes v - 2**bits, so the maximum representable value
      becomes -1).

  In every other configuration -- request matching the stored signedness, or an
  absent/uninterpretable request -- the element values are returned unchanged.
  When a sentinel fill value accompanies the array, it is reinterpreted by the
  very same fixed-width rule whenever (and only whenever) the elements are.

The reinterpretation is the two's-complement correspondence between the signed
and unsigned views of one fixed-width integer: writing `modulus = 2**bits`, the
unsigned view of v is `v mod modulus` and the signed view of v is
`((v + modulus/2) mod modulus) - modulus/2`. The width is conveyed as that
`modulus` (a power of two, at least 2).

Integer values are modelled directly as `int` (this is an integer-domain
behaviour, not a floating-point one); a data array is a `List[int]` of its
per-element values. The fixed-width reinterpretation `reinterpret` is modelled
deeply as a verified arithmetic function, whose equality to the real
element-wise array conversion is checked out-of-band by axiom_check.py (G-AX),
not consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No consumed @ContractOnly axioms: the only opaque callee is the *changed*
#  element transform, which is therefore modelled deeply below -- an
#  A-reference validated against the real array conversion by axiom_check.py,
#  per SPEC_GUIDE section 3 -- rather than axiomatized.)
# axioms-end


# pure-start
# Stored signedness of the incoming array.
KIND_SIGNED = 0
KIND_UNSIGNED = 1
# Requested target signedness (the out-of-band attribute).
ATTR_FALSE = 0
ATTR_TRUE = 1
ATTR_OTHER = 2


@Pure
def reinterpret(v: int, modulus: int, to_signed: bool) -> int:
    """The fixed-width reinterpretation of one integer between the signed and
    unsigned views of the same bit pattern. `modulus == 2**bits`.

    * to_signed: produce the signed view -- values at/above the half-range fold
      down by `modulus`, so the unsigned maximum `modulus-1` becomes `-1`.
    * not to_signed: produce the unsigned view -- negative values fold up by
      `modulus`, so `-1` becomes `modulus-1`.
    """
    Requires(modulus >= 2)
    if to_signed:
        if v >= modulus // 2:
            return v - modulus
        return v
    else:
        if v < 0:
            return v + modulus
        return v


@Pure
def reinterpret_seq(s: PSeq[int], modulus: int, to_signed: bool) -> PSeq[int]:
    """Element-wise reinterpretation of a whole array, front-recursive so a
    single unfold is available to callers per loop step."""
    Requires(modulus >= 2)
    if len(s) == 0:
        return PSeq(0).take(0)
    return PSeq(reinterpret(s[0], modulus, to_signed)) + \
        reinterpret_seq(s.drop(1), modulus, to_signed)


@Pure
def transform_to_signed(kind: int, unsigned: int) -> bool:
    """The decode produces the SIGNED view exactly when an unsigned-stored array
    is requested to be treated as signed."""
    return kind == KIND_UNSIGNED and unsigned == ATTR_FALSE


@Pure
def transform_to_unsigned(kind: int, unsigned: int) -> bool:
    """The decode produces the UNSIGNED view exactly when a signed-stored array
    is requested to be treated as unsigned."""
    return kind == KIND_SIGNED and unsigned == ATTR_TRUE


@Pure
def is_transformed(kind: int, unsigned: int) -> bool:
    """Whether decode reinterprets the elements at all."""
    return transform_to_signed(kind, unsigned) or \
        transform_to_unsigned(kind, unsigned)


@Pure
def fill_out(kind: int, unsigned: int, modulus: int, fill: int) -> int:
    """The decoded sentinel fill value: reinterpreted by the same fixed-width
    rule as the elements when the array is transformed, else unchanged. Stated
    as a pure projection so the postconditions can pin it without a second
    mutable output."""
    Requires(modulus >= 2)
    if transform_to_signed(kind, unsigned):
        return reinterpret(fill, modulus, True)
    elif transform_to_unsigned(kind, unsigned):
        return reinterpret(fill, modulus, False)
    else:
        return fill
# pure-end


def reconcile_signedness(data: List[int], kind: int, unsigned: int,
                         modulus: int, has_fill: bool,
                         fill: int) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(data), 1 / 2))
    Requires(kind == KIND_SIGNED or kind == KIND_UNSIGNED)
    Requires(unsigned == ATTR_FALSE or unsigned == ATTR_TRUE or
             unsigned == ATTR_OTHER)
    Requires(modulus >= 2)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(data), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The decoded array is the element-wise fixed-width reinterpretation when
    # the request disagrees with the stored signedness, else the array
    # unchanged. The signed-view case (unsigned-stored, requested signed) is the
    # behaviour the issue demands; the unsigned-view case is its symmetric
    # counterpart; every other configuration is a pass-through.
    Ensures(Implies(transform_to_signed(kind, unsigned),
                    ToSeq(Result()) == reinterpret_seq(ToSeq(data), modulus,
                                                       True)))
    Ensures(Implies(transform_to_unsigned(kind, unsigned),
                    ToSeq(Result()) == reinterpret_seq(ToSeq(data), modulus,
                                                       False)))
    Ensures(Implies(not is_transformed(kind, unsigned),
                    ToSeq(Result()) == ToSeq(data)))
    # The sentinel fill value is reinterpreted by exactly the same rule iff the
    # elements are (and is reported alongside the decoded array).
    Ensures(Implies(has_fill and transform_to_signed(kind, unsigned),
                    fill_out(kind, unsigned, modulus, fill) ==
                    reinterpret(fill, modulus, True)))
    Ensures(Implies(has_fill and transform_to_unsigned(kind, unsigned),
                    fill_out(kind, unsigned, modulus, fill) ==
                    reinterpret(fill, modulus, False)))
    Ensures(Implies(has_fill and not is_transformed(kind, unsigned),
                    fill_out(kind, unsigned, modulus, fill) == fill))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    if transform_to_signed(kind, unsigned):
        # unsigned-stored array, requested signed -> signed view of each element
        i = len(data)
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(data), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(data))
            Invariant(ToSeq(result) ==
                      reinterpret_seq(ToSeq(data).drop(i), modulus, True))
            Invariant(MustTerminate(i + 1))
            # invariants-end
            Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
            Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
            result = [reinterpret(data[i - 1], modulus, True)] + result
            i = i - 1
    elif transform_to_unsigned(kind, unsigned):
        # signed-stored array, requested unsigned -> unsigned view of each elem
        i = len(data)
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(data), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(data))
            Invariant(ToSeq(result) ==
                      reinterpret_seq(ToSeq(data).drop(i), modulus, False))
            Invariant(MustTerminate(i + 1))
            # invariants-end
            Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
            Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
            result = [reinterpret(data[i - 1], modulus, False)] + result
            i = i - 1
    else:
        # request matches storage or is absent/uninterpretable: pass through
        i = len(data)
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(data), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(data))
            Invariant(ToSeq(result) == ToSeq(data).drop(i))
            Invariant(MustTerminate(i + 1))
            # invariants-end
            Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
            Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
            result = [data[i - 1]] + result
            i = i - 1
    return result
    # impl-end
