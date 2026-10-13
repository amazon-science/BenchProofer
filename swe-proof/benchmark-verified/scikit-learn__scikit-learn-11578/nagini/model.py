"""Twin-artifact model for scikit-learn__scikit-learn-11578.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A cross-validation helper computes a score for fitted multiclass logistic
  coefficients by handing them to a throw-away scoring estimator and asking a
  scorer for a number. The classifier supports two multiclass modes, selected
  by a flag ``multi_class``:

    * the one-vs-rest mode normalises a per-class logistic response, and
    * the multinomial mode applies a softmax to the per-class decision scores.

  The two modes induce DIFFERENT class-probability vectors from the same
  per-class decision scores (they agree only degenerately).

  The behaviour that matters: the scoring estimator the helper builds must use
  the SAME ``multi_class`` mode that the helper itself was asked to operate in.
  Consequently a probability-consuming scorer (one that reads the predicted
  class-probability vector) sees the multinomial probabilities when the helper
  runs in multinomial mode — NOT the one-vs-rest probabilities.

Modelling choices (Nagini fragment):
  * The multiclass mode is an ``int`` tag: ``OVR`` (0) and ``MULTINOMIAL`` (1).
  * The per-class decision scores of one test sample are a ``PSeq[int]`` (the
    real per-class real-valued decision row, refined to integer code points;
    only the SELECTION between the two probability transforms is the behaviour
    under specification, so the transforms are opaque references validated
    against their real numeric callees out-of-band by axiom_check.py / G-AX).
  * The two probability transforms ``proba_softmax`` and ``proba_ovr`` are
    distinct total functions of the decision row that DIFFER on a witness row.

No string indexing is used (Nagini bans it). Markers (machine-parsed) delimit
the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def proba_softmax(d: PSeq[int]) -> PSeq[int]:
    """The multinomial class-probability vector induced by the per-class
    decision row ``d`` (the softmax transform). Opaque reference: its real
    numeric callee and its distinctness from the one-vs-rest transform are
    validated by axiom_check.py (G-AX). See mapping.md."""
    Ensures(len(Result()) == len(d))


@Pure
@ContractOnly
def proba_ovr(d: PSeq[int]) -> PSeq[int]:
    """The one-vs-rest class-probability vector induced by the per-class
    decision row ``d`` (normalised per-class logistic response). Opaque
    reference validated by axiom_check.py (G-AX). See mapping.md."""
    Ensures(len(Result()) == len(d))


@Pure
@ContractOnly
def witness_decision() -> PSeq[int]:
    """A per-class decision row on which the two probability transforms
    genuinely differ — the situation a multiclass test exercises. Existence is
    witnessed by axiom_check.py running the real transforms (G-AX)."""
    Ensures(len(Result()) >= 2)


@Pure
@ContractOnly
def transforms_differ() -> bool:
    """The two probability transforms are NOT the same function: on the witness
    decision row they yield different probability vectors. Validated against the
    real softmax / one-vs-rest callees by axiom_check.py (G-AX)."""
    Ensures(Implies(Result(), proba_softmax(witness_decision())
                    != proba_ovr(witness_decision())))
# axioms-end


# pure-start
OVR = 0          # the one-vs-rest multiclass mode tag
MULTINOMIAL = 1  # the multinomial (softmax) multiclass mode tag


@Pure
def scoring_proba(mode: int, d: PSeq[int]) -> PSeq[int]:
    """The class-probability vector the scoring estimator produces for a test
    sample with per-class decision row ``d`` when operating in ``mode``: the
    softmax (multinomial) transform in multinomial mode, otherwise the
    one-vs-rest transform."""
    if mode == MULTINOMIAL:
        return proba_softmax(d)
    return proba_ovr(d)
# pure-end


def scoring_estimator_proba(caller_mode: int, d: PSeq[int]) -> PSeq[int]:
    # pre-conditions-start
    Requires(caller_mode == OVR or caller_mode == MULTINOMIAL)
    # The two probability transforms genuinely differ on the witness row (the
    # audited reference, G-AX).
    Requires(transforms_differ())
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The scoring estimator runs in the SAME mode the helper was asked for, so
    # the probability vector it produces is that mode's transform of ``d``.
    Ensures(Result() == scoring_proba(caller_mode, d))
    # The discriminating consequence: in multinomial mode the probability
    # vector is the multinomial (softmax) one ...
    Ensures(Implies(caller_mode == MULTINOMIAL, Result() == proba_softmax(d)))
    # ... and in one-vs-rest mode it is the one-vs-rest one.
    Ensures(Implies(caller_mode == OVR, Result() == proba_ovr(d)))
    # Therefore, on a decision row where the two transforms differ, a
    # multinomial-mode score is NOT the one-vs-rest probability vector that the
    # default (mode-ignoring) estimator would have produced.
    Ensures(Implies(caller_mode == MULTINOMIAL and d == witness_decision(),
                    Result() != proba_ovr(d)))
    # post-conditions-end
    # impl-start
    # The scoring estimator inherits the caller's multiclass mode, so its
    # probability output is that mode's transform of the decision row.
    effective_mode = caller_mode  # type: int
    result = scoring_proba(effective_mode, d)  # type: PSeq[int]
    return result
    # impl-end
