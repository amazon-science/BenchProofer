#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-11578.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same inputs and comparing the observable output — the
probability method the scored estimator applies:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python via the mapping.md §2 bijection:
                  probabilityMethodForScoring(requested) = probaMethodOf(requested)
                      'ovr'         -> 'ovrNormalize'
                      'multinomial' -> 'softmax'
  * ORACLE  — patch.diff's behaviour: the REAL patched
              `sklearn.linear_model.logistic._log_reg_scoring_path` run
              in-container. We isolate the CHANGED op (which probability method
              scores the fold) from the unchanged downstream by passing a probe
              `scoring` callable that, when the routine calls
              `scoring(log_reg, X_test, y_test)` (logistic.py:958), inspects the
              estimator it was handed and records which `predict_proba` branch it
              actually takes — recomputing OvR-normalize vs softmax from the
              estimator's own decision_function and seeing which one
              predict_proba equals. That recorded method is the oracle.

Thus the only thing observed is the changed flag-propagation: the probability
method the scored estimator uses, exactly the R/I content of the impl (§4.1).
The dropped `fit_intercept` kwarg (refinement.md §B) is inert and never observed.

They must agree for every requested mode. Exit 0 iff zero disagreements; any
disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), against the repo at
base_commit with patch.diff applied (the harness applies it before this runs).
numpy + sklearn only. The fuzz seed is pinned (mapping.md §4).
"""
import random
import sys

import numpy as np

from sklearn.datasets import make_classification
from sklearn.linear_model.logistic import _log_reg_scoring_path
from sklearn.utils.extmath import softmax

SEED = 11578
# Each oracle config runs a REAL lbfgs fit inside _log_reg_scoring_path
# (~3 ms measured in-container), so a 10^5 sweep completes in ~5 min — well
# inside the container budget. The changed behaviour is a pure function of a
# BINARY flag (the requested mode): the R/I shadow does not even read the
# dataset. We still fuzz the dataset shape/seed across 10^5 configs (both modes)
# to mechanically confirm the probability-method selection is
# dataset-INDEPENDENT — i.e. no shape/seed produces a disagreement.
N_FUZZ = 100_000      # randomized (n_samples, n_features, n_classes, seed) configs


# --- the R/I shadow: Solution.lean probabilityMethodForScoring ---------------
def shadow_method(requested):
    """probaMethodOf(requested), transliterated (mapping.md §2)."""
    return "ovrNormalize" if requested == "ovr" else "softmax"


# --- oracle instrumentation: which predict_proba branch did the fold use? ----
# Faithful reconstruction of both predict_proba branches from the estimator's
# own decision_function, mirroring the real code EXACTLY (logistic.py:1343-1353
# for softmax; base.py:280 `_predict_proba_lr` for ovr), including the ndim==1
# handling that the ovr-mode fold (classes_=[-1,1], 1-D decision) exercises.
def _ovr_predict_proba(decision):
    prob = 1.0 / (1.0 + np.exp(-decision))
    if prob.ndim == 1:
        return np.vstack([1 - prob, prob]).T
    prob = prob / prob.sum(axis=1).reshape((prob.shape[0], -1))
    return prob


def _softmax_predict_proba(decision):
    if decision.ndim == 1:
        decision_2d = np.c_[-decision, decision]
    else:
        decision_2d = decision
    return softmax(np.array(decision_2d, dtype=np.float64), copy=True)


def _observed_branch(clf, X):
    decision = clf.decision_function(X)
    observed = clf.predict_proba(X)
    is_ovr = np.allclose(observed, _ovr_predict_proba(decision), atol=1e-10)
    is_softmax = np.allclose(observed, _softmax_predict_proba(decision),
                             atol=1e-10)
    if is_ovr and is_softmax:
        return "both"
    if is_ovr:
        return "ovrNormalize"
    if is_softmax:
        return "softmax"
    return "neither"


def oracle_method(n_samples, n_features, n_classes, requested, ds_seed):
    """Run the REAL patched _log_reg_scoring_path; the probe scorer records the
    probability method the estimator handed to scoring(...) actually uses."""
    X, y = make_classification(n_samples=n_samples, n_features=n_features,
                               n_informative=max(3, n_features - 1),
                               n_redundant=0, n_classes=n_classes,
                               random_state=ds_seed)
    train = np.arange(0, int(n_samples * 0.8))
    test = np.arange(int(n_samples * 0.8), n_samples)

    recorded = {}

    def probe_scoring(estimator, X_test, y_test):
        # the routine calls this at logistic.py:958 with the constructed log_reg
        recorded["method"] = _observed_branch(estimator, X_test)
        return 0.0  # value irrelevant; we only observe the branch

    # How LogisticRegressionCV actually drives this routine (logistic.py
    # ~1645): for 'multinomial' it makes ONE call with pos_class=None (the path
    # fits the full multinomial model); for 'ovr' it loops over the classes and
    # makes one call PER class with pos_class=that class. With >2 classes,
    # logistic_regression_path raises 'To fit OvR, use the pos_class argument'
    # unless pos_class is supplied (logistic.py:604-609). So in ovr mode we must
    # pin a pos_class — we take the first training class, exactly one leg of the
    # per-class OvR loop. The scored estimator's mode (and hence the probability
    # method observed) is identical across legs, so one leg suffices.
    pos_class = None
    if requested == "ovr":
        pos_class = np.unique(y[train])[0]
    # lbfgs supports multinomial; Cs=[1.] keeps it to a single fit.
    _log_reg_scoring_path(X, y, train, test, pos_class=pos_class, Cs=[1.],
                          scoring=probe_scoring, fit_intercept=True,
                          solver="lbfgs", multi_class=requested, max_iter=50)
    return recorded.get("method", "neither")


def fuzz_configs(n, pyrng):
    modes = ["ovr", "multinomial"]
    # boundary: both modes over a few class/feature/sample shapes
    for mode in modes:
        for (ns, nf, nc) in [(60, 6, 3), (80, 6, 3), (100, 8, 4),
                             (90, 5, 3), (120, 10, 5)]:
            yield ns, nf, nc, mode, 0
    for _ in range(n):
        mode = pyrng.choice(modes)
        nc = pyrng.randint(3, 6)               # multiclass: methods differ
        nf = pyrng.randint(nc + 1, 12)
        ns = pyrng.randint(40, 200)
        yield ns, nf, nc, mode, pyrng.randint(0, 10_000)


def main():
    pyrng = random.Random(SEED)
    disagreements = []
    count = 0
    for ns, nf, nc, mode, ds_seed in fuzz_configs(N_FUZZ, pyrng):
        count += 1
        shadow = shadow_method(mode)
        oracle = oracle_method(ns, nf, nc, mode, ds_seed)
        if shadow != oracle:
            disagreements.append((ns, nf, nc, mode, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d configs:"
              % (len(disagreements), count))
        for ns, nf, nc, mode, sh, orc in disagreements:
            print("  n_samples=%d n_features=%d n_classes=%d mode=%s "
                  "shadow=%s oracle=%s" % (ns, nf, nc, mode, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of probabilityMethodForScoring agrees with "
          "patch.diff behaviour (real _log_reg_scoring_path probability method) "
          "on %d configs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
