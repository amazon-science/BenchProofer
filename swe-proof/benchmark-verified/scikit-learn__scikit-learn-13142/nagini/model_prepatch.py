"""Twin-artifact model for scikit-learn__scikit-learn-13142.

Behaviour under specification (a self-standing behavioural contract):

  A labelling routine runs over several independent trials. Each trial yields a
  parameter configuration together with a score; the routine selects, across
  the trials, the configuration whose score is largest (the earliest such
  configuration when several tie for the largest score), and that selected
  configuration is the configuration the object holds when the routine returns.

  The labels the routine returns are the deterministic label assignment of the
  configuration the object holds on return — i.e. exactly the labels a
  subsequent labelling query against that same object would itself produce. So
  the labels obtained while fitting agree with the labels obtained by querying
  the fitted object, for every number of trials.

A parameter configuration is modelled by an integer identifier; a trial's score
is modelled by an integer (the selection depends only on the order of the
scores, not their magnitudes). The deterministic assignment of labels from a
configuration — the unchanged query primitive — is axiomatized as a pure
function of the configuration identifier (`labels_of`).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class Estimator:
    def __init__(self, config: int) -> None:
        Ensures(Acc(self.config) and self.config == config)  # type: ignore
        self.config = config


# axioms-start
@Pure
@ContractOnly
def labels_of(config: int) -> int:
    """Deterministic label assignment derived from a parameter configuration
    (the unchanged query primitive). It is a pure function of the configuration
    identifier alone: the same configuration always yields the same labels, so
    two evaluations against equal configurations agree. Provenance + executable
    soundness check: mapping.md / axiom_check.py.
    """
# axioms-end


# pure-start
@Pure
def best_score(score: PSeq[int]) -> int:
    """The largest score among a non-empty run of trials."""
    Requires(len(score) >= 1)
    if len(score) == 1:
        return score[0]
    rest = best_score(score.drop(1))
    if score[0] >= rest:
        return score[0]
    return rest


@Pure
def best_config(config: PSeq[int], score: PSeq[int]) -> int:
    """The configuration of the highest-scoring trial; on ties the earliest
    such trial wins. Front-recursive so a single unfold is available per step."""
    Requires(len(config) == len(score))
    Requires(len(score) >= 1)
    if len(score) == 1:
        return config[0]
    if score[0] >= best_score(score.drop(1)):
        return config[0]
    return best_config(config.drop(1), score.drop(1))
# pure-end


def fit_and_label(inst: Estimator, run_config: List[int],
                  run_score: List[int]) -> int:
    # pre-conditions-start
    Requires(Acc(inst.config))
    Requires(Acc(list_pred(run_config), 1 / 2))
    Requires(Acc(list_pred(run_score), 1 / 2))
    Requires(len(run_config) == len(run_score))
    Requires(len(run_config) >= 1)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(inst.config))
    Ensures(Acc(list_pred(run_config), 1 / 2))
    Ensures(Acc(list_pred(run_score), 1 / 2))
    Ensures(len(run_config) == len(run_score) and len(run_config) >= 1)
    # On return the object holds the selected (highest-scoring,
    # earliest-on-tie) configuration.
    Ensures(inst.config == best_config(ToSeq(run_config), ToSeq(run_score)))
    # The returned labels are the deterministic label assignment of the
    # configuration the object holds on return, so a subsequent labelling query
    # against that object agrees with the labels returned here.
    Ensures(Result() == labels_of(inst.config))
    # post-conditions-end
    # impl-start
    n = len(run_config)
    # The transient configuration the object holds after the final trial is the
    # final trial's configuration (may differ from the selected one).
    inst.config = run_config[n - 1]
    # Select the highest-scoring (earliest-on-tie) configuration over all trials
    # by scanning the trials from last to first; the running selection equals
    # best_config / best_score over the already-scanned suffix.
    selected = run_config[n - 1]  # type: int
    selected_score = run_score[n - 1]  # type: int
    i = n
    while i > 1:
        # invariants-start
        Invariant(Acc(inst.config))
        Invariant(Acc(list_pred(run_config), 1 / 2))
        Invariant(Acc(list_pred(run_score), 1 / 2))
        Invariant(len(run_config) == n and len(run_score) == n)
        Invariant(1 <= i and i <= n)
        Invariant(selected_score == best_score(ToSeq(run_score).drop(i - 1)))
        Invariant(selected == best_config(ToSeq(run_config).drop(i - 1),
                                          ToSeq(run_score).drop(i - 1)))
        # invariants-end
        Assert(ToSeq(run_score).drop(i - 2)[0] == run_score[i - 2])
        Assert(ToSeq(run_config).drop(i - 2)[0] == run_config[i - 2])
        Assert(ToSeq(run_score).drop(i - 2).drop(1) == ToSeq(run_score).drop(i - 1))
        Assert(ToSeq(run_config).drop(i - 2).drop(1) == ToSeq(run_config).drop(i - 1))
        s = run_score[i - 2]
        if s >= selected_score:
            selected = run_config[i - 2]
            selected_score = s
        i = i - 1
    # Derive the labels from the transient configuration the object currently
    # holds, THEN persist the selected configuration.
    labels = labels_of(inst.config)
    inst.config = selected
    return labels
    # impl-end
