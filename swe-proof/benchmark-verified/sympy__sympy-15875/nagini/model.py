"""Twin-artifact model for sympy__sympy-15875.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A commutative sum decides whether it is zero from a classification of its
  summands. Each summand falls into exactly one class:

    0  real and known-zero
    1  real and known-nonzero
    2  real with undetermined zeroness
    3  purely imaginary
    4  "imaginary-or-zero" (not classified imaginary, but i*summand is real)
    5  none of the above

  The combined verdict is a three-valued answer (``True`` = the sum is zero,
  ``False`` = the sum is provably nonzero, ``None`` = undecidable):

    * If any summand is class 2 or class 5 the sum is undecidable (``None``).
    * If every summand is class 0 the sum is zero (``True``).
    * Otherwise let ``k`` be the number of class-1 (real-nonzero) summands.
      The real-nonzero summands are themselves summed into a sub-expression
      whose three-valued zeroness is ``sub_is_zero``.
        - If there are NO real-nonzero summands, or if EVERY summand is a
          real-nonzero summand, the verdict is undecidable (``None``): in
          either case the real part carries no information that can be combined
          with the imaginary classes to settle the question.
        - Otherwise the verdict follows the zeroness of the real-nonzero
          sub-expression combined with the imaginary classes:
            sub is zero  & no imaginary class at all      -> True
            sub is zero  & some class-3 and no class-4     -> False
            sub provably nonzero                           -> False
            anything else                                  -> None

The empty sub-expression (no real-nonzero summands) is itself zero, so when
``k == 0`` the input ``sub_is_zero`` is necessarily ``True``; this is required
as a precondition linking the two inputs.

Summands are modelled as a ``List[int]`` of class tags (sympy objects and
their assumption queries are opaque to Nagini). The three-valued zeroness of an
expression is modelled as ``Optional[bool]`` (``None`` = undecided). The pure
sequence theory ``PSeq[int]`` carries the specification via front-recursive
folds (a count and an existence test over the class tags).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No @ContractOnly axioms: the opaque recursive sub-expression zeroness is
#  passed in as the three-valued parameter `sub_is_zero`; it is not a callee
#  this module names or computes.)
# axioms-end


# pure-start
@Pure
def count_eq(s: PSeq[int], c: int) -> int:
    """Number of elements of `s` equal to `c` (front-recursive fold)."""
    if len(s) == 0:
        return 0
    return (1 if s[0] == c else 0) + count_eq(s.drop(1), c)


@Pure
def has_eq(s: PSeq[int], c: int) -> bool:
    """Whether any element of `s` equals `c` (front-recursive fold)."""
    if len(s) == 0:
        return False
    return s[0] == c or has_eq(s.drop(1), c)
# pure-end


def add_is_zero(classes: List[int], sub_is_zero: Optional[bool]) -> Optional[bool]:
    # pre-conditions-start
    Requires(Acc(list_pred(classes), 1 / 2))
    # every summand carries a class tag in 0..5
    Requires(Forall(int, lambda i: (Implies(0 <= i and i < len(classes),
        0 <= classes[i] and classes[i] <= 5), [[classes[i]]])))
    # the empty real-nonzero sub-expression is itself zero
    Requires(Implies(count_eq(ToSeq(classes), 1) == 0,
        sub_is_zero is not None and sub_is_zero))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(classes), 1 / 2))
    # an undecidable summand (class 2 or 5) forces the undecidable verdict
    Ensures(Implies(has_eq(ToSeq(classes), 2) or has_eq(ToSeq(classes), 5),
        Result() is None))
    # all summands known-zero -> the sum is zero
    Ensures(Implies(not (has_eq(ToSeq(classes), 2) or has_eq(ToSeq(classes), 5))
        and count_eq(ToSeq(classes), 0) == len(classes), Result() is not None and Result()))
    # no real-nonzero information, or it is the whole sum -> undecidable
    Ensures(Implies(not (has_eq(ToSeq(classes), 2) or has_eq(ToSeq(classes), 5))
        and count_eq(ToSeq(classes), 0) != len(classes)
        and (count_eq(ToSeq(classes), 1) == 0
             or count_eq(ToSeq(classes), 1) == len(classes)), Result() is None))
    # the discriminating clause: real-nonzero sub-expression is zero, with only
    # imaginary classes present -> the whole sum is provably nonzero (False)
    Ensures(Implies(not (has_eq(ToSeq(classes), 2) or has_eq(ToSeq(classes), 5))
        and count_eq(ToSeq(classes), 0) != len(classes)
        and count_eq(ToSeq(classes), 1) != 0
        and count_eq(ToSeq(classes), 1) != len(classes)
        and sub_is_zero is not None and sub_is_zero
        and has_eq(ToSeq(classes), 3) and not has_eq(ToSeq(classes), 4),
        Result() is not None and not Result()))
    # real-nonzero sub-expression is zero, with no imaginary class at all -> zero
    Ensures(Implies(not (has_eq(ToSeq(classes), 2) or has_eq(ToSeq(classes), 5))
        and count_eq(ToSeq(classes), 0) != len(classes)
        and count_eq(ToSeq(classes), 1) != 0
        and count_eq(ToSeq(classes), 1) != len(classes)
        and sub_is_zero is not None and sub_is_zero
        and not has_eq(ToSeq(classes), 3) and not has_eq(ToSeq(classes), 4),
        Result() is not None and Result()))
    # real-nonzero sub-expression provably nonzero -> the whole sum is nonzero
    Ensures(Implies(not (has_eq(ToSeq(classes), 2) or has_eq(ToSeq(classes), 5))
        and count_eq(ToSeq(classes), 0) != len(classes)
        and count_eq(ToSeq(classes), 1) != 0
        and count_eq(ToSeq(classes), 1) != len(classes)
        and sub_is_zero is not None and not sub_is_zero,
        Result() is not None and not Result()))
    # real-nonzero sub-expression undecided -> the whole sum is undecidable
    Ensures(Implies(not (has_eq(ToSeq(classes), 2) or has_eq(ToSeq(classes), 5))
        and count_eq(ToSeq(classes), 0) != len(classes)
        and count_eq(ToSeq(classes), 1) != 0
        and count_eq(ToSeq(classes), 1) != len(classes)
        and sub_is_zero is None,
        Result() is None))
    # real-nonzero sub-expression is zero but some imaginary-or-zero class is
    # present -> the imaginary part carries no settling information (undecidable)
    Ensures(Implies(not (has_eq(ToSeq(classes), 2) or has_eq(ToSeq(classes), 5))
        and count_eq(ToSeq(classes), 0) != len(classes)
        and count_eq(ToSeq(classes), 1) != 0
        and count_eq(ToSeq(classes), 1) != len(classes)
        and sub_is_zero is not None and sub_is_zero
        and has_eq(ToSeq(classes), 4),
        Result() is None))
    # post-conditions-end
    # impl-start
    z = 0
    nz = 0
    im = False
    im_or_z = False
    has2 = False
    has5 = False
    n = len(classes)
    i = n
    # backward scan: the suffix drop(i) aligns with the front-recursive folds,
    # so each step prepends classes[i-1] and unfolds count_eq/has_eq once.
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(classes), 1 / 2))
        Invariant(0 <= i and i <= n and n == len(classes))
        Invariant(Forall(int, lambda j: (Implies(0 <= j and j < len(classes),
            0 <= classes[j] and classes[j] <= 5), [[classes[j]]])))
        Invariant(z == count_eq(ToSeq(classes).drop(i), 0))
        Invariant(nz == count_eq(ToSeq(classes).drop(i), 1))
        Invariant(im == has_eq(ToSeq(classes).drop(i), 3))
        Invariant(im_or_z == has_eq(ToSeq(classes).drop(i), 4))
        Invariant(has2 == has_eq(ToSeq(classes).drop(i), 2))
        Invariant(has5 == has_eq(ToSeq(classes).drop(i), 5))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        c = classes[i - 1]
        Assert(ToSeq(classes).drop(i - 1)[0] == c)
        Assert(ToSeq(classes).drop(i - 1).drop(1) == ToSeq(classes).drop(i))
        if c == 0:
            z = z + 1
        elif c == 1:
            nz = nz + 1
        elif c == 2:
            has2 = True
        elif c == 3:
            im = True
        elif c == 4:
            im_or_z = True
        else:
            has5 = True
        i = i - 1
    Assert(ToSeq(classes).drop(0) == ToSeq(classes))
    if has2 or has5:
        return None
    if z == n:
        return True
    if nz == 0 or nz == n:
        return None
    if sub_is_zero is None:
        return None
    if sub_is_zero:
        if not im_or_z and not im:
            return True
        if im and not im_or_z:
            return False
        return None
    return False
    # impl-end
