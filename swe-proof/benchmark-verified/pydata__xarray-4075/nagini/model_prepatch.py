"""Twin-artifact model for pydata__xarray-4075.

Behaviour under specification (stated as the desired behaviour, not as an edit):

  A weighted total counts how much trustworthy weight backs a set of samples.
  Each sample i carries a presence flag `mask[i]` (1 if the datum is present,
  0 if it is missing) and an associated weight `weights[i]` (a non-negative
  integer; a boolean weight is the special case of the values 0/1). The total
  is the weighted reduction `sum_i mask[i] * weights[i]` — the arithmetic sum
  of the weights of the present samples — computed by the array dot product of
  the presence flags and the weights.

  The decisive requirement: this total is a genuine numeric COUNT, never a mere
  presence indicator. When several present samples each carry weight 1 the total
  must accumulate them (e.g. two present unit weights total 2), and it must do so
  identically whether the weights were supplied as a boolean array or as a
  numeric array — the element type of the weights must not collapse the sum to a
  0/1 "any present" answer.

Modelling: the presence mask is `mask: List[int]` of 0/1; the weights are
`weights: List[int]` of non-negative integers (booleans being 0/1);
`weights_are_bool` records whether the weight array's element type is boolean.
The array dot product is the unchanged community callee `dot_reduce`, whose
contraction is numeric when handed a numeric operand and boolean-saturating when
BOTH operands are boolean. The numeric and boolean contractions are spelled out
deeply as the front-recursive folds `int_dot` / `bool_dot` (validated == the real
dot by axiom_check.py / G-AX). The specification is carried by `PSeq[int]`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def dot_reduce(mask: PSeq[int], weights: PSeq[int], boolean_dot: bool) -> int:
    """The array dot-product reduction (the unchanged community callee) of the
    presence flags `mask` and the `weights`, contracted over the shared axis.

    The contraction semantics depend ONLY on whether it runs in boolean
    arithmetic (`boolean_dot`), which happens exactly when BOTH operands have a
    boolean element type:

      * numeric contraction (`boolean_dot` false — a numeric operand is present,
        as the desired behaviour always arranges): the genuine arithmetic sum
        `sum_i mask[i] * weights[i]` (`int_dot`).
      * boolean contraction (`boolean_dot` true — both operands boolean): the
        SATURATING logical reduction, 1 iff some position has both flags set,
        else 0 (`bool_dot`); it cannot exceed 1.

    Weakest contract the proof needs. Provenance + executable soundness check:
    mapping.md / axiom_check.py.
    """
    Requires(len(mask) == len(weights))
    Ensures(Implies(not boolean_dot, Result() == int_dot(mask, weights)))
    Ensures(Implies(boolean_dot, Result() == bool_dot(mask, weights)))
# axioms-end


# pure-start
@Pure
def int_dot(mask: PSeq[int], weights: PSeq[int]) -> int:
    """Numeric dot-product reduction: the arithmetic sum of the present samples'
    weights, `sum_i mask[i] * weights[i]`. Front-recursive (one unfold per loop
    step — the canonical sequence-fold pattern)."""
    Requires(len(mask) == len(weights))
    if len(mask) == 0:
        return 0
    return mask[0] * weights[0] + int_dot(mask.drop(1), weights.drop(1))


@Pure
def bool_dot(mask: PSeq[int], weights: PSeq[int]) -> int:
    """Boolean (saturating) dot-product reduction: 1 iff some position has both
    flags set, else 0. The logical OR over positions of (mask[i] AND
    weights[i]), with 0/1 operands modelled by min (AND) and max (OR).
    Front-recursive."""
    Requires(len(mask) == len(weights))
    if len(mask) == 0:
        return 0
    head = 1 if (mask[0] >= 1 and weights[0] >= 1) else 0
    return head if head >= bool_dot(mask.drop(1), weights.drop(1)) \
        else bool_dot(mask.drop(1), weights.drop(1))
# pure-end


def sum_of_weights_value(
    mask: List[int], weights: List[int], weights_are_bool: bool
) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(mask), 1 / 2))
    Requires(Acc(list_pred(weights), 1 / 2))
    Requires(len(mask) == len(weights))
    Requires(len(ToSeq(mask)) == len(ToSeq(weights)))
    # presence flags and (the boolean case of) the weights are 0/1; the numeric
    # case allows any non-negative integer weight.
    Requires(Forall(int, lambda i: (Implies(0 <= i and i < len(mask),
                                             mask[i] == 0 or mask[i] == 1),
                                     [[mask[i]]])))
    Requires(Forall(int, lambda i: (Implies(0 <= i and i < len(weights),
                                             weights[i] >= 0),
                                     [[weights[i]]])))
    Requires(Implies(weights_are_bool,
                     Forall(int, lambda i: (Implies(0 <= i and i < len(weights),
                                                     weights[i] == 0 or weights[i] == 1),
                                            [[weights[i]]]))))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(mask), 1 / 2))
    Ensures(Acc(list_pred(weights), 1 / 2))
    Ensures(len(ToSeq(mask)) == len(ToSeq(weights)))
    # The total is the genuine arithmetic weighted count of the present samples,
    # independent of whether the weights were boolean or numeric.
    Ensures(Result() == int_dot(ToSeq(mask), ToSeq(weights)))
    # post-conditions-end
    # impl-start
    # Pre-patch: hand the weight array to the dot unchanged. A boolean weight
    # array then meets the (always-boolean) presence mask in a boolean
    # contraction, which saturates to 0/1 instead of counting.
    boolean_dot = weights_are_bool
    result = dot_reduce(ToSeq(mask), ToSeq(weights), boolean_dot)
    return result
    # impl-end
