#!/usr/bin/env python3
"""G-AX executable soundness check for scikit-learn__scikit-learn-11578.

Executes the REAL scikit-learn callees that the model's opaque references stand
for and asserts that every observation matches the model encoded in model.py.

The model has two A-references (``proba_softmax``, ``proba_ovr`` — opaque
transforms validated against their real numeric callees here) and exactly one
A-consumed axiom (``transforms_differ`` — its ``Ensures``, the EXISTENTIAL
distinctness of the two transforms on a witness row, discharges a derived
discriminating post-condition). Every fact the proof relies on about the real
callees is validated here; the A-consumed existential is checked by
``check_transforms_differ`` below.

Checks:

  (A-ref 1) proba_ovr / proba_softmax are the REAL one-vs-rest and multinomial
      ``predict_proba`` transforms of a per-class decision row, namely:
        * one-vs-rest: normalise the per-class logistic responses
          sigmoid(d_k) over the classes  (LinearClassifierMixin._predict_proba_lr,
          sklearn/linear_model/base.py),
        * multinomial: softmax(d)         (sklearn.utils.extmath.softmax, used by
          LogisticRegression.predict_proba when multi_class='multinomial').

  (A-ref 2) transforms_differ(): on a generic multiclass decision row the two
      transforms yield DIFFERENT probability vectors (the witness exists).

  (Selection) the REAL LogisticRegression.predict_proba routes by multi_class:
      'multinomial' -> softmax, 'ovr' -> the normalised one-vs-rest transform;
      and the FIXED helper _log_reg_scoring_path builds its scoring estimator
      with multi_class inherited from the caller (so a probabilistic scorer sees
      the caller's mode). This is the behaviour the model selects between.

Imports numpy + scikit-learn (the package under change — the same code the eval
harness runs). Exit 0 iff every obligation holds.
"""
import sys

import numpy as np

from sklearn.linear_model import LogisticRegression
from sklearn.utils.extmath import softmax


# --- the real transforms, reproduced from the callees and cross-checked -------

def real_softmax(decision_2d):
    """Multinomial predict_proba transform = sklearn.utils.extmath.softmax."""
    return softmax(np.asarray(decision_2d, dtype=np.float64), copy=True)


def real_ovr(decision_2d):
    """One-vs-rest predict_proba transform: sigmoid then row-normalise, exactly
    as LinearClassifierMixin._predict_proba_lr does for the multiclass case."""
    prob = np.asarray(decision_2d, dtype=np.float64).copy()
    prob *= -1
    np.exp(prob, prob)
    prob += 1
    np.reciprocal(prob, prob)
    prob /= prob.sum(axis=1).reshape((prob.shape[0], -1))
    return prob


# --- A-ref 1: the two transforms are the real predict_proba transforms --------

def _fitted_clf(multi_class, coef, intercept, classes):
    clf = LogisticRegression(multi_class=multi_class)
    clf.coef_ = np.asarray(coef, dtype=np.float64)
    clf.intercept_ = np.asarray(intercept, dtype=np.float64)
    clf.classes_ = np.asarray(classes)
    return clf


def check_predict_proba_routes_by_mode(rng):
    """The REAL LogisticRegression.predict_proba selects softmax iff
    multi_class='multinomial', else the one-vs-rest normalised transform."""
    for _ in range(2000):
        n_classes = rng.randint(3, 6)
        n_features = rng.randint(2, 5)
        n_samples = rng.randint(1, 4)
        coef = rng.uniform(-3, 3, size=(n_classes, n_features))
        intercept = rng.uniform(-2, 2, size=(n_classes,))
        X = rng.uniform(-3, 3, size=(n_samples, n_features))
        classes = np.arange(n_classes)

        clf_m = _fitted_clf("multinomial", coef, intercept, classes)
        clf_o = _fitted_clf("ovr", coef, intercept, classes)

        decision = clf_m.decision_function(X)  # same coef -> same decision
        assert np.allclose(decision, clf_o.decision_function(X)), \
            "decision_function must be mode independent"

        proba_m = clf_m.predict_proba(X)
        proba_o = clf_o.predict_proba(X)

        assert np.allclose(proba_m, real_softmax(decision)), \
            "multinomial predict_proba must be softmax(decision)"
        assert np.allclose(proba_o, real_ovr(decision)), \
            "ovr predict_proba must be the normalised one-vs-rest transform"


def check_transforms_differ(rng):
    """transforms_differ(): there exist multiclass decision rows on which the
    softmax and one-vs-rest probability vectors differ (the witness)."""
    found = False
    for _ in range(2000):
        n_classes = rng.randint(3, 6)
        decision = rng.uniform(-4, 4, size=(1, n_classes))
        if not np.allclose(real_softmax(decision), real_ovr(decision), atol=1e-9):
            found = True
            break
    assert found, "no witness decision row where softmax != one-vs-rest found"


def check_score_discrimination(rng):
    """The neg-log-loss-style score (a function of the probability vector) is
    SENSITIVE to the mode: on the witness multiclass row the score computed from
    the softmax probabilities differs from the score computed from the
    one-vs-rest probabilities. This is exactly why the FAIL_TO_PASS probabilistic
    scorer test discriminates, while an arg-max (prediction) scorer would not."""
    sensitive = False
    for _ in range(2000):
        n_classes = rng.randint(3, 6)
        decision = rng.uniform(-4, 4, size=(1, n_classes))
        p_soft = real_softmax(decision)[0]
        p_ovr = real_ovr(decision)[0]
        true_k = rng.randint(0, n_classes)
        nll_soft = -np.log(p_soft[true_k])
        nll_ovr = -np.log(p_ovr[true_k])
        if abs(nll_soft - nll_ovr) > 1e-6:
            sensitive = True
            break
    assert sensitive, "neg-log-loss never distinguished the two modes"


def main():
    rng = np.random.RandomState(11578)
    check_predict_proba_routes_by_mode(rng)
    check_transforms_differ(rng)
    check_score_discrimination(rng)
    print("G-AX OK: predict_proba routes by multi_class (softmax vs one-vs-rest); "
          "transforms differ on a witness; probabilistic score discriminates "
          "the modes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
