"""Twin-artifact model for astropy__astropy-14995.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A binary array operation combines two operands and must decide the array of
  per-element flags ("mask") carried by the result. Each operand may carry such
  a flag array or carry none at all. A combiner callable, when supplied, merges
  two present flag arrays element-by-element. The required result is:

    (1) no flags at all when neither operand carries flags, or when no combiner
        was supplied;
    (2) a copy of the *other* operand's flag array when this operand carries no
        flags but the other one does;
    (3) a copy of *this* operand's flag array when this operand carries flags
        and the other operand carries none — the lone present array is
        propagated unchanged, never combined against a missing array;
    (4) the element-wise combination of the two flag arrays (the combiner
        applied to both) when both operands carry them.

  The decision is symmetric in the two operands when only one carries flags:
  whichever operand has a flag array, that array (copied) is the result, and it
  must reach the result intact regardless of which side it came from. In
  particular case (3) is decided by the OTHER operand's flag array being absent,
  independently of any other attribute of that operand.

Flag arrays are modelled as ``List[int]`` (a bitmask of non-negative ints).
"Carries flags" / "carries none" is the boolean ``has_mask``. The decision
returns a small carrier (``MaskResult``) whose ``present`` flag says whether the
result has flags and whose ``data`` holds them when it does — the faithful
``Optional`` "mask or None" return. The element-wise combiner callable is the
UNCHANGED callee that is *invoked* in case (4); it is axiomatized opaquely as
``combine_masks`` (a per-element fold over equal-length arrays preserving the
shape) and its materializing call as ``apply_combiner``. Its soundness against
the real callee is checked by axiom_check.py (G-AX). The decision under
specification is the branch selection (cases 1-3), where the combiner is NOT
called; case (4) merely defers to the unchanged combiner.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class Operand:
    """The second operand: a minimal object carrying only its flag array.
    ``has_mask`` is False when the operand carries no flags; ``mask`` then holds
    no meaningful content (it is never read in that case)."""

    def __init__(self, has_mask: bool, mask: List[int]) -> None:
        Requires(Acc(list_pred(mask), 1 / 2))
        Ensures(Acc(self.has_mask) and self.has_mask == has_mask)  # type: ignore
        Ensures(Acc(self.mask) and self.mask is mask)  # type: ignore
        Ensures(Acc(list_pred(self.mask), 1 / 2))  # type: ignore
        self.has_mask = has_mask
        self.mask = mask


class MaskResult:
    """The decided result mask: ``present`` is False for "no flags" (the
    ``None`` mask); when True, ``data`` holds the flag array."""

    def __init__(self, present: bool, data: List[int]) -> None:
        Requires(Acc(list_pred(data), 1 / 2))
        Ensures(Acc(self.present) and self.present == present)  # type: ignore
        Ensures(Acc(self.data) and self.data is data)  # type: ignore
        Ensures(Acc(list_pred(self.data), 1 / 2))  # type: ignore
        Ensures(ToSeq(self.data) == ToSeq(data))  # type: ignore
        self.present = present
        self.data = data


# axioms-start
@Pure
@ContractOnly
def combine_masks(a: PSeq[int], b: PSeq[int]) -> PSeq[int]:
    """The unchanged element-wise combiner callable, applied to two present
    equal-length flag arrays (case 4 only — it is NEVER invoked when one array
    is absent). The weakest contract the proof needs: the combination has the
    same shape (length) as its inputs. Provenance + executable soundness check:
    mapping.md / axiom_check.py."""
    Ensures(Implies(len(a) == len(b), len(Result()) == len(a)))


@ContractOnly
def apply_combiner(a: List[int], b: List[int]) -> List[int]:
    """Materializing call to the unchanged combiner callable: returns a freshly
    allocated flag array whose content is exactly the abstract combination of
    the two inputs. Same callee as `combine_masks`; this is its impure (list-
    producing) face used inside the implementation. G-AX checks both against the
    real callee."""
    Requires(Acc(list_pred(a), 1 / 2))
    Requires(Acc(list_pred(b), 1 / 2))
    Requires(len(ToSeq(a)) == len(ToSeq(b)))
    Ensures(Acc(list_pred(a), 1 / 2))
    Ensures(Acc(list_pred(b), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == combine_masks(ToSeq(a), ToSeq(b)))
# axioms-end


# pure-start
# (No auxiliary pure spec functions: the combiner is opaque, axiomatized above;
# the branch selection cases 1-3 are stated directly over the flag arrays.)
# pure-end


def result_mask(
    self_has_mask: bool,
    self_mask: List[int],
    operand: Operand,
    handle_mask_present: bool,
) -> MaskResult:
    # pre-conditions-start
    Requires(Acc(list_pred(self_mask), 1 / 2))
    Requires(Acc(operand.has_mask, 1 / 2) and Acc(operand.mask, 1 / 2))
    Requires(Acc(list_pred(operand.mask), 1 / 2))
    # The two operands wrap co-shaped data, so their flag arrays are stored at
    # the same shape (the combiner is defined on equal-length arrays). This
    # holds regardless of which operand currently carries flags.
    Requires(len(ToSeq(self_mask)) == len(ToSeq(operand.mask)))
    # pre-conditions-end
    # post-conditions-start
    # read-only inputs are returned with their permission and value intact.
    Ensures(Acc(list_pred(self_mask), 1 / 2))
    Ensures(Acc(operand.has_mask, 1 / 2) and Acc(operand.mask, 1 / 2))
    Ensures(Acc(list_pred(operand.mask), 1 / 2))
    Ensures(operand.has_mask == Old(operand.has_mask)
            and operand.mask is Old(operand.mask))
    # the result carrier is fully formed.
    Ensures(Acc(Result().present) and Acc(Result().data)
            and Acc(list_pred(Result().data), 1 / 2))

    # (1) no flags when neither operand carries flags, or when no combiner.
    Ensures(Implies(not handle_mask_present, not Result().present))
    Ensures(Implies(handle_mask_present and not self_has_mask
                    and not operand.has_mask,
                    not Result().present))

    # (2) this operand has no flags, the other does: copy the other's array.
    Ensures(Implies(handle_mask_present and not self_has_mask
                    and operand.has_mask,
                    Result().present
                    and ToSeq(Result().data) == ToSeq(operand.mask)))

    # (3) this operand carries flags and the other carries none: the lone
    # present array is copied through unchanged, NOT combined against a missing
    # array. The decision turns on the OTHER operand's flag array being absent.
    Ensures(Implies(handle_mask_present and self_has_mask
                    and not operand.has_mask,
                    Result().present
                    and ToSeq(Result().data) == ToSeq(self_mask)))

    # (4) both operands carry flags: the element-wise combination, i.e. exactly
    # the unchanged combiner applied to both present arrays.
    Ensures(Implies(handle_mask_present and self_has_mask and operand.has_mask,
                    Result().present
                    and ToSeq(Result().data) == combine_masks(ToSeq(self_mask),
                                                              ToSeq(operand.mask))))
    # post-conditions-end
    # impl-start
    empty = []  # type: List[int]
    if (not self_has_mask and not operand.has_mask) or not handle_mask_present:
        return MaskResult(False, empty)
    elif not self_has_mask:
        c = copy_seq(operand.mask)
        return MaskResult(True, c)
    else:
        # Pre-patch: the guard that would propagate this operand's lone flag
        # array tests the other operand OBJECT's absence, which never holds here
        # (the other operand object is always present), so a present-but-flag-
        # less other operand falls through to the combiner with its absent
        # flags instead of yielding this operand's array.
        c = apply_combiner(self_mask, operand.mask)
        return MaskResult(True, c)
    # impl-end


def copy_seq(xs: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(xs), 1 / 2))
    Requires(MustTerminate(10))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(xs), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == ToSeq(xs))
    # post-conditions-end
    # impl-start
    out = []  # type: List[int]
    i = 0
    while i < len(xs):
        # invariants-start
        Invariant(Acc(list_pred(xs), 1 / 2))
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= i and i <= len(xs))
        Invariant(ToSeq(out) == ToSeq(xs).take(i))
        Invariant(MustTerminate(len(xs) - i + 1))
        # invariants-end
        out.append(xs[i])
        Assert(ToSeq(xs).take(i + 1) == ToSeq(xs).take(i) + PSeq(xs[i]))
        i = i + 1
    Assert(ToSeq(xs).take(len(xs)) == ToSeq(xs))
    return out
    # impl-end
