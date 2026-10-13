#!/usr/bin/env python3
"""Reference soundness witness for scikit-learn__scikit-learn-10297.

This bundle has NO @ContractOnly axioms and NO A-reference deep models of an
unchanged callee: both modelled behaviours are the *changed* code, modelled
directly (see refinement.md). G-AX is therefore vacuous. This script is a
reference witness rather than an axiom check: it runs the REAL (post-patch)
`sklearn.linear_model.RidgeClassifierCV` and asserts that the two modelled
behaviours hold of the real estimator.

  (1) configure_classifier_cv: the constructor accepts `store_cv_values` and
      forwards it, so the configured estimator's retention flag equals what the
      caller requested:
          RidgeClassifierCV(store_cv_values=v).store_cv_values == v
      (pre-patch: TypeError -- unexpected keyword argument).

  (2) stored_cv_values: when retention is on, after fit the retained
      cross-validation values are a rank-3 array with shape
      (n_samples, n_targets, n_alphas) -- the target axis always present, even
      for a binary (n_targets == 1) classification target.

Imports only numpy and sklearn (the repo under test). Exit 0 iff every
observation matches the model.
"""
import sys

import numpy as np
from sklearn.linear_model import RidgeClassifierCV


def check_flag_forwarded():
    """(1) The requested retention flag is forwarded to the configured engine."""
    for v in (True, False):
        est = RidgeClassifierCV(alphas=[0.1, 1.0, 10.0], store_cv_values=v)
        assert est.store_cv_values == v, (
            "store_cv_values not forwarded: requested %r, estimator has %r"
            % (v, est.store_cv_values))


def check_shape(X, y, alphas):
    """(2) With retention on, cv_values_ is rank-3 (n_samples, n_targets, n_alphas)."""
    n_samples = X.shape[0]
    n_alphas = len(alphas)
    r = RidgeClassifierCV(alphas=alphas, store_cv_values=True)
    r.fit(X, y)
    shape = r.cv_values_.shape
    assert r.cv_values_.ndim == 3, (
        "cv_values_ not rank 3 for classifier: shape=%r" % (shape,))
    assert shape[0] == n_samples, (
        "axis 0 (samples) wrong: %r expected %d" % (shape, n_samples))
    assert shape[2] == n_alphas, (
        "axis 2 (penalties) wrong: %r expected %d" % (shape, n_alphas))
    # axis 1 (targets) is always present; >= 1
    assert shape[1] >= 1, "target axis missing: %r" % (shape,)
    return shape


def main():
    check_flag_forwarded()

    # --- F2P boundary cases (mirrors test_ridge_classifier_cv_store_cv_values) ---
    X = np.array([[-1.0, -1.0], [-1.0, 0.0], [-0.8, -1.0],
                  [1.0, 1.0], [1.0, 0.0]])

    # binary target -> label-binarized to a single column -> n_targets == 1
    y_bin = np.array([1, 1, 1, -1, -1])
    alphas = [1e-1, 1e0, 1e1]
    shape = check_shape(X, y_bin, alphas)
    assert shape == (5, 1, 3), "binary classifier cv_values_ shape: %r" % (shape,)

    # multilabel/multitarget -> n_targets == number of columns
    y_multi = np.array([[1, 1, 1, -1, -1],
                        [1, -1, 1, -1, 1],
                        [-1, -1, 1, -1, -1]]).transpose()
    shape = check_shape(X, y_multi, alphas)
    assert shape == (5, 3, 3), "multilabel classifier cv_values_ shape: %r" % (shape,)

    # --- fuzz: vary n_samples, n_features, n_classes, n_alphas ----------------
    rng = np.random.RandomState(10297)
    n_checks = 0
    for _ in range(200):
        n_samples = int(rng.randint(6, 20))
        n_features = int(rng.randint(2, 6))
        n_alphas = int(rng.randint(1, 5))
        alphas = list(np.logspace(-2, 2, n_alphas))
        Xf = rng.randn(n_samples, n_features)

        # binary target with both classes guaranteed present
        yb = rng.randint(0, 2, size=n_samples)
        yb[0] = 0
        yb[1] = 1
        s = check_shape(Xf, yb, alphas)
        assert s[1] == 1 and s == (n_samples, 1, n_alphas), (
            "binary fuzz shape wrong: %r" % (s,))
        n_checks += 1

        # multilabel target (each column an indicator)
        ncls = int(rng.randint(2, 5))
        Ym = rng.randint(0, 2, size=(n_samples, ncls))
        # guarantee each column has both 0 and 1 so it stays an active target
        Ym[0, :] = 0
        Ym[1, :] = 1
        s = check_shape(Xf, Ym, alphas)
        assert s == (n_samples, ncls, n_alphas), (
            "multilabel fuzz shape wrong: %r (n_targets expected %d)" % (s, ncls))
        n_checks += 1

    print("REFERENCE-WITNESS OK: store_cv_values forwarded; classifier "
          "cv_values_ rank-3 (n_samples, n_targets, n_alphas) on F2P boundary "
          "+ %d fuzz fits" % n_checks)
    return 0


if __name__ == "__main__":
    sys.exit(main())
