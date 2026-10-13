"""Twin-artifact model for scikit-learn__scikit-learn-26194.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A receiver-operating-characteristic computation finishes by prepending one
  extra leading entry to the descending sequence of decision thresholds, so the
  plotted curve is anchored at the origin (the leading entry corresponds to the
  degenerate operating point where no instance is predicted positive).

  The desired leading threshold is the POSITIVE-INFINITY sentinel: a single
  value that is correct regardless of the scale of the scores (which may be
  arbitrary decision values or probability estimates confined to the unit
  interval). The remaining thresholds are returned unchanged and in the same
  order.

So, given the finite descending thresholds `thresholds`, the result is the list
whose first element is the positive-infinity sentinel and whose remaining
elements are exactly `thresholds` in order.

The thresholds are modelled as a `List[float]` of interpreted real numbers
(verified with `--float-encoding=real`), since the distinguishing behaviour is
the real-number identity of the anchoring entry. Two unchanged numeric
primitives carry the infinity theory: `pos_inf` is the positive-infinity
sentinel and `is_pos_inf` tests whether a real number is that sentinel; their
provenance and executable soundness check are in mapping.md / axiom_check.py.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def is_pos_inf(x: float) -> bool:
    """Test whether a real number is the positive-infinity sentinel. An unchanged
    numeric primitive (the is-infinite test) the routine relies on; opaque
    predicate. Provenance + executable soundness check: mapping.md /
    axiom_check.py."""
    pass


@Pure
@ContractOnly
def pos_inf() -> float:
    """The positive-infinity sentinel. An unchanged numeric primitive the routine
    prepends as the anchoring threshold; it satisfies `is_pos_inf`. Provenance +
    executable soundness check: mapping.md / axiom_check.py."""
    Ensures(is_pos_inf(Result()))
# axioms-end


# pure-start
# (no pure helpers needed)
# pure-end


def anchor_thresholds(thresholds: List[float]) -> List[float]:
    # pre-conditions-start
    # The descending decision thresholds are the distinct finite scores; the
    # sequence is non-empty. Read-only input: fractional permission.
    Requires(Acc(list_pred(thresholds), 1 / 2))
    Requires(len(thresholds) >= 1)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(thresholds), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # Exactly one extra leading entry is prepended.
    Ensures(len(Result()) == len(thresholds) + 1)
    # The leading anchoring threshold is the positive-infinity sentinel.
    Ensures(is_pos_inf(Result()[0]))
    # Every remaining threshold is returned unchanged, in the same order.
    Ensures(ToSeq(Result()).drop(1) == ToSeq(thresholds))
    # post-conditions-end
    # impl-start
    # PRE-PATCH (buggy) skeleton: the anchoring threshold is the largest score
    # nudged upward by one (a FINITE value), instead of the positive-infinity
    # sentinel. For probability-estimate scores this finite value can land above
    # the natural unit-interval upper bound.
    lead = thresholds[0] + 1.0
    result = [lead]  # type: List[float]
    i = 0
    while i < len(thresholds):
        # invariants-start
        Invariant(Acc(list_pred(thresholds), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(thresholds))
        Invariant(len(result) == i + 1)
        Invariant(ToSeq(result).take(1) == PSeq(lead))
        Invariant(ToSeq(result).drop(1) == ToSeq(thresholds).take(i))
        Invariant(MustTerminate(len(thresholds) - i + 1))
        # invariants-end
        result.append(thresholds[i])
        i = i + 1
    return result
    # impl-end
