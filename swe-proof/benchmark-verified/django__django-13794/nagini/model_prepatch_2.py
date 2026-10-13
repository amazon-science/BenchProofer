"""Twin-artifact model for django__django-13794.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A deferred (lazy) value must combine under binary `+` from EITHER side with
  an ordinary operand, using its realized (forced) value, so that the `add`
  filter concatenates rather than collapsing to the empty string.

  (1) With the lazy value on the LEFT, the result is the realized value
      followed by the other operand: `realized ++ other`.
  (2) With the lazy value on the RIGHT, the result is the other operand
      followed by the realized value: `other ++ realized`.

  In both cases the result is the ordinary `+` (sequence concatenation) of the
  two operands once the lazy value is realized; nothing is dropped and the
  operand order is preserved.

Sequence values (the realized value and the other operand) are modelled as
`List[int]` of Unicode code points (Nagini bans `str` indexing); the
specification is carried by `PSeq[int]` via `ToSeq`, and `+` is sequence
concatenation. The realized value (the forced evaluation of the lazy value) is
the read-only input `realized`.

Two combination directions are modelled, each as its own contracted function
(the per-function pre/post/invariant/impl regions repeat). No callee is
axiomatized: the forcing of the deferred value is an R-refinement (the realized
value is the input), and the only operation is concatenation, modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no axioms: the realized value is a read-only input — an R-refinement of the
# unchanged forcing call — and the modelled operation is concatenation, spelled
# out deeply in the impl regions; the only callee, the forcing of the deferred
# value, is unchanged and its result is that input.)
# axioms-end


# pure-start
# (no pure helpers: the specification is stated directly over PSeq[int]
# concatenation via ToSeq.)
# pure-end


def forward_combine(realized: List[int], other: List[int]) -> List[int]:
    """Lazy-value-on-the-left `+`: the realized value followed by `other`."""
    # pre-conditions-start
    Requires(Acc(list_pred(realized), 1 / 2))
    Requires(Acc(list_pred(other), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(realized), 1 / 2))
    Ensures(Acc(list_pred(other), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is the concatenation realized ++ other, in that order.
    Ensures(ToSeq(Result()) == ToSeq(realized) + ToSeq(other))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = 0
    while i < len(realized):
        # invariants-start
        Invariant(Acc(list_pred(realized), 1 / 2))
        Invariant(Acc(list_pred(other), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(realized))
        Invariant(ToSeq(result) == ToSeq(realized).take(i))
        Invariant(MustTerminate(len(realized) - i + 1))
        # invariants-end
        result.append(realized[i])
        i = i + 1
    j = 0
    while j < len(other):
        # invariants-start
        Invariant(Acc(list_pred(realized), 1 / 2))
        Invariant(Acc(list_pred(other), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(other))
        Invariant(ToSeq(result) == ToSeq(realized) + ToSeq(other).take(j))
        Invariant(MustTerminate(len(other) - j + 1))
        # invariants-end
        result.append(other[j])
        j = j + 1
    return result
    # impl-end


def reverse_combine(realized: List[int], other: List[int]) -> List[int]:
    """Lazy-value-on-the-right `+`: `other` followed by the realized value."""
    # pre-conditions-start
    Requires(Acc(list_pred(realized), 1 / 2))
    Requires(Acc(list_pred(other), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(realized), 1 / 2))
    Ensures(Acc(list_pred(other), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is the concatenation other ++ realized, in that order.
    Ensures(ToSeq(Result()) == ToSeq(other) + ToSeq(realized))
    # post-conditions-end
    # impl-start
    # Pre-patch: the right-operand (reflected) `+` is not provided, so the left
    # operand's `+` raises and the surrounding caller collapses the outcome to
    # the empty sequence rather than the concatenation.
    result = []  # type: List[int]
    return result
    # impl-end
