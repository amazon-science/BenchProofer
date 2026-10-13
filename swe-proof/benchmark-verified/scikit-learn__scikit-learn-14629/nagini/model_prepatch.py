"""Twin-artifact model for scikit-learn__scikit-learn-14629.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A multi-output classifier wraps one fitted single-output sub-classifier per
  target column. After fitting, the wrapper must expose the per-output class
  labels as an ordered collection — one entry per sub-classifier, in the same
  order as the sub-classifiers, each entry carrying exactly the class labels
  that the corresponding sub-classifier learned.

  The desired guarantee is therefore that this collection:

    (1) has exactly as many entries as there are fitted sub-classifiers (one
        per output), and

    (2) at every position holds the class labels of the sub-classifier at that
        position — element-for-element the same labels: position ``i`` carries
        the labels of sub-classifier ``i`` (not a reordering, not a subset, not
        a constant, not the labels of a different output).

  A wrapper that leaves this collection unpopulated (so an output position has
  no class labels at all) is exactly the defect this specification forbids: a
  consumer that walks the per-output class labels must find, at each position,
  the labels of the corresponding sub-classifier.

The fitted sub-classifiers are modelled as a read-only ``List[Estimator]``,
each ``Estimator`` exposing only the touched facet — the class labels it learned
for its output, modelled as a pure label-sequence value (``PSeq[int]``, the
sequence of class-label codes; element values are the discriminator, matching
how a consumer compares the per-output labels). The produced collection is a
``List[PSeq[int]]``; the per-position guarantee is element-wise value equality
between ``Result()[i]`` and the labels of sub-classifier ``i`` — pinning each
entry to the genuine per-output labels rather than to a constant, a reordering,
or another output's labels.

No callee is axiomatized: the gathering is pure per-element structural logic,
modelled deeply. Markers (machine-parsed) delimit the spec / proof / impl
regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class Estimator:
    """One fitted single-output sub-classifier, exposing only the touched
    facet: ``cls_vals``, the sequence of class-label codes it learned for its
    output (read-only here). Its element values are the discriminator: a
    consumer compares the per-output labels element-for-element."""

    def __init__(self, cls_vals: PSeq[int]) -> None:
        Ensures(Acc(self.cls_vals) and self.cls_vals == cls_vals)  # type: ignore
        self.cls_vals = cls_vals  # type: PSeq[int]


# axioms-start
# (No consumed axioms. The added behaviour — gathering each fitted
# sub-classifier's class labels into one ordered per-output collection — is
# pure per-element structural logic, modelled DEEPLY by the verified loop below.
# The unchanged fitting step that produces the sub-classifiers is not re-derived:
# the already-fitted list is taken as input, so no callee is axiomatized.)
# axioms-end


# pure-start
@Pure
def est_vals(e: Estimator) -> PSeq[int]:
    """The class labels of one fitted sub-classifier, as a pure label-sequence
    value — the per-output labels position ``i`` of the produced collection must
    carry. Reads the touched facet at a fractional permission (read-only)."""
    Requires(Acc(e.cls_vals, 1 / 4))
    return e.cls_vals
# pure-end


def gather_output_classes(estimators: List[Estimator]) -> List[PSeq[int]]:
    # pre-conditions-start
    # The fitted sub-classifier list is READ-ONLY here (the gathering iterates
    # over it without mutating it): its spine and each sub-classifier's touched
    # facet are required at fractional permission (directive 5).
    Requires(Acc(list_pred(estimators), 1 / 2))
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(estimators),
        Acc(estimators[k].cls_vals, 1 / 4)))))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The input list is left exactly as it was (returned at the same fractional
    # permission), so the operation cannot satisfy the spec by mutating it.
    Ensures(Acc(list_pred(estimators), 1 / 2))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(estimators),
        Acc(estimators[k].cls_vals, 1 / 4)))))
    Ensures(Acc(list_pred(Result())))
    # (1) one entry per fitted sub-classifier.
    Ensures(len(Result()) == len(estimators))
    # (2) position i carries exactly the class labels of sub-classifier i —
    # element-for-element value equality (the property a consumer of the
    # per-output labels observes): not a reordering, not a subset, not a
    # constant, not another output's labels.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(estimators),
        Result()[k] == est_vals(estimators[k])))))
    # post-conditions-end
    # impl-start
    # PRE-PATCH SKELETON: the wrapper has no fit override that gathers the
    # per-output class labels, so this collection is left UNPOPULATED — exactly
    # the pre-patch state in which a fitted multi-output classifier carried no
    # per-output class-label collection at all. The empty result violates
    # postcondition (1) (len(Result()) == len(estimators)) for any fitted
    # wrapper (one or more outputs), which is precisely the spec sensing the bug.
    result = []  # type: List[PSeq[int]]
    return result
    # impl-end
