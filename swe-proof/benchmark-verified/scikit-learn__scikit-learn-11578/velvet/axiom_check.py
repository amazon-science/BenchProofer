#!/usr/bin/env python3
"""G-AX executable soundness check for scikit-learn__scikit-learn-11578.

Validates the single kind-A leg of refinement.md: the **A-reference** deep model
`probaMethodOf` (Solution.lean `pure` region) against the REAL unchanged callee
`sklearn.linear_model.LogisticRegression.predict_proba`'s mode selection.

`probaMethodOf` (the deep model):

    probaMethodOf(ovr)         = ovrNormalize
    probaMethodOf(multinomial) = softmax

Soundness claim (A-reference): for a fitted `LogisticRegression` carrying
`multi_class=m` (m in {'ovr','multinomial'} — the domain `_log_reg_scoring_path`
admits), the probability method `predict_proba` actually applies equals
`probaMethodOf(m)` under the mapping.md §2 bijection:

  * 'ovr'         -> the per-class logistic + cross-class normalization
                     (`_predict_proba_lr`): prob = 1/(1+exp(-decision)), then
                     prob /= prob.sum(axis=1);
  * 'multinomial' -> softmax(decision_2d).

We do NOT trust a label: we recompute BOTH candidate formulas from the
estimator's own `decision_function(X)` and check which one `predict_proba(X)`
actually equals. That observed method must match `probaMethodOf(m)`. This is the
double-mask-free check: we observe the branch at the level the model claims it
(which probability transform), not by reading `self.multi_class` back.

Exercised over boundary + randomized fuzz coefficient matrices / class counts,
on the multiclass (2-D decision) shape the F2P test uses. The two methods are
genuinely distinct there (for >2 classes softmax != OvR-normalize), so the check
has discriminating power.

Imports only `numpy` and the repo (`sklearn`). Runs in-container against the
prebuilt instance image. Exit 0 iff every obligation holds.
"""
import random
import sys

import numpy as np

from sklearn.linear_model import LogisticRegression
from sklearn.utils.extmath import softmax


# --- Solution.lean `pure` region, transliterated (kept in lock-step) ---------
# MultiClass bijection (mapping.md §2) and probaMethodOf.
def proba_method_of(multi_class):
    """Reference of Solution.lean `probaMethodOf` over MultiClass."""
    return "ovrNormalize" if multi_class == "ovr" else "softmax"


# --- the two real probability transforms, recomputed from decision scores ----
def ovr_normalize(decision_2d):
    """`_predict_proba_lr` for the multiclass (2-D) case (base.py:280)."""
    prob = 1.0 / (1.0 + np.exp(-decision_2d))
    prob /= prob.sum(axis=1).reshape((prob.shape[0], -1))
    return prob


def softmax_method(decision_2d):
    """The `else` branch of predict_proba (logistic.py:1353)."""
    return softmax(np.array(decision_2d, dtype=np.float64), copy=True)


def observed_method(clf, X):
    """Recompute both candidate formulas from the estimator's own
    decision_function and report which one predict_proba actually equals.
    Returns 'ovrNormalize', 'softmax', 'both' (indistinguishable) or 'neither'."""
    decision = clf.decision_function(X)
    if decision.ndim == 1:
        decision_2d = np.c_[-decision, decision]
    else:
        decision_2d = decision
    observed = clf.predict_proba(X)
    is_ovr = np.allclose(observed, ovr_normalize(decision_2d), atol=1e-10)
    is_softmax = np.allclose(observed, softmax_method(decision_2d), atol=1e-10)
    if is_ovr and is_softmax:
        return "both"
    if is_ovr:
        return "ovrNormalize"
    if is_softmax:
        return "softmax"
    return "neither"


def make_estimator(multi_class, n_classes, n_features, rng):
    """A fitted-shaped LogisticRegression: coef_/intercept_ set directly, exactly
    as `_log_reg_scoring_path` sets them on the estimator it hands to the scorer
    (logistic.py:945-952). No actual fit needed — predict_proba reads coef_,
    intercept_ and multi_class only."""
    clf = LogisticRegression(multi_class=multi_class)
    clf.coef_ = rng.uniform(-3, 3, size=(n_classes, n_features))
    clf.intercept_ = rng.uniform(-2, 2, size=(n_classes,))
    clf.classes_ = np.arange(n_classes)
    return clf


def check_one(multi_class, n_classes, n_features, n_samples, rng):
    clf = make_estimator(multi_class, n_classes, n_features, rng)
    X = rng.uniform(-3, 3, size=(n_samples, n_features))
    observed = observed_method(clf, X)
    expected = proba_method_of(multi_class)
    # For >2 classes the two transforms differ, so 'both' must not occur; we
    # require the observed method to be exactly the one the model predicts.
    assert observed == expected, (
        "probaMethodOf A-reference unsound: multi_class=%r over %d classes, "
        "%d features: real predict_proba uses %r, deep model requires %r"
        % (multi_class, n_classes, n_features, observed, expected))


def main():
    rng = np.random.default_rng(11578)
    pyrng = random.Random(11578)

    modes = ["ovr", "multinomial"]

    # --- discriminating-power guard: confirm the two methods actually differ --
    # on a representative multiclass instance, so the check is not vacuous.
    probe = make_estimator("ovr", 3, 5, np.random.default_rng(1))
    Xp = np.random.default_rng(2).uniform(-3, 3, size=(7, 5))
    dec = probe.decision_function(Xp)
    assert not np.allclose(ovr_normalize(dec), softmax_method(dec)), (
        "G-AX self-test failed: OvR-normalize and softmax coincide on the probe "
        "— the check would be vacuous")

    # --- boundary: every mode x several class/feature/sample shapes -----------
    n_boundary = 0
    for mode in modes:
        for (nc, nf, ns) in [(3, 5, 20), (3, 6, 100), (4, 3, 10),
                             (5, 8, 50), (10, 4, 30), (3, 2, 1)]:
            check_one(mode, nc, nf, ns, rng)
            n_boundary += 1

    # --- randomized fuzz ------------------------------------------------------
    n_fuzz = 4000
    for _ in range(n_fuzz):
        mode = pyrng.choice(modes)
        nc = pyrng.randint(3, 12)        # >2 classes: the two methods differ
        nf = pyrng.randint(1, 10)
        ns = pyrng.randint(1, 40)
        check_one(mode, nc, nf, ns, rng)

    print("G-AX OK: probaMethodOf deep model (== real "
          "LogisticRegression.predict_proba branch selection) sound on %d "
          "boundary + %d fuzz estimators across modes %s; OvR-normalize vs "
          "softmax confirmed distinct on the multiclass probe"
          % (n_boundary, n_fuzz, modes))
    return 0


if __name__ == "__main__":
    sys.exit(main())
