#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-11578
(nagini).

SHADOW  — the impl region of model.py, copied VERBATIM below with the
          contract calls (Requires/Ensures) stripped; the @Pure selector
          `scoring_proba` copies over as a plain function. The two
          @ContractOnly probability transforms call the REAL repo callees
          they stand for per mapping.md section 3:
            proba_softmax -> sklearn.utils.extmath.softmax applied to the
                             per-class decision scores (the multinomial
                             probability transform), with the same 1-d ->
                             two-column decision widening the repo transform
                             applies;
            proba_ovr     -> LinearClassifierMixin._predict_proba_lr invoked
                             directly on the scoring estimator (the
                             one-vs-rest transform: per-class logistic
                             response, row-normalised), which bypasses any
                             mode routing by construction.

BRIDGE  — mapping.md section 2: the multiclass mode string maps to the int
          tag (one-vs-rest <-> 0, multinomial <-> 1); the PSeq[int] decision
          and probability rows are refined back to the real float rows, and
          shadow/oracle probability rows compare with a tight relative
          tolerance (both sides are the same float pipeline).

ORACLE  — the REAL patched cross-validation scoring helper (PYTHONPATH=
          /testbed, gold patch applied by the gate before this script runs):
          the path-scoring function of the logistic module, driven with a
          recording scorer. For every fitted coefficient vector along the
          path the scorer receives the throw-away scoring estimator; the
          recorded observable is the class-probability matrix that estimator
          hands a probability-consuming scorer. Each probability ROW (one
          test sample, one path point, one mode) is one comparison.

Input domain: the modeled precondition is mode in {0, 1} plus the audited
transforms-differ reference (established by G-AX); decision rows are free.
Configurations vary class count (2..5), feature count, sample count,
intercept fitting, path length and class separation, and both modes.

>= 1e5 Requires-satisfying inputs: probability-row comparisons accumulated
across configurations until >= 100000 (boundary configurations first).
Pinned seed: 11578.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + numpy + the repo package only.
"""
import sys
import warnings

import numpy as np

SEED = 11578
TARGET_ROWS = 100_000

# ---------------------------------------------------------------------------
# Real-callee bindings for the @ContractOnly transforms (mapping.md sec. 3).
# Each call receives the scoring estimator and the test matrix captured at
# scoring time; the decision row(s) are read off the estimator itself.
# ---------------------------------------------------------------------------


def proba_softmax(est, X):
    from sklearn.utils.extmath import softmax
    decision = est.decision_function(X)
    if decision.ndim == 1:
        decision_2d = np.c_[-decision, decision]
    else:
        decision_2d = decision
    return softmax(decision_2d, copy=True)


def proba_ovr(est, X):
    from sklearn.linear_model.base import LinearClassifierMixin
    return LinearClassifierMixin._predict_proba_lr(est, X)


# ---------------------------------------------------------------------------
# model.py pure region + impl region, VERBATIM with contract statement lines
# (Requires/Ensures) stripped. The carrier (mode, d) is realised as
# (mode, (est, X)) through the bridge: d is the estimator's per-class
# decision row for each test sample.
# ---------------------------------------------------------------------------

OVR = 0          # the one-vs-rest multiclass mode tag
MULTINOMIAL = 1  # the multinomial (softmax) multiclass mode tag


def scoring_proba(mode, d):
    if mode == MULTINOMIAL:
        return proba_softmax(*d)
    return proba_ovr(*d)


def scoring_estimator_proba(caller_mode, d):
    # The scoring estimator inherits the caller's multiclass mode, so its
    # probability output is that mode's transform of the decision row.
    effective_mode = caller_mode
    result = scoring_proba(effective_mode, d)
    return result


# ---------------------------------------------------------------------------
# Differential harness.
# ---------------------------------------------------------------------------


def make_data(rng, n_classes, n_features, n_samples, sep):
    """Linearly-structured multiclass data (no fitting subtleties needed —
    the comparison is on the scoring transform, not fit quality)."""
    centers = rng.uniform(-sep, sep, size=(n_classes, n_features))
    y = rng.randint(0, n_classes, size=n_samples)
    X = centers[y] + rng.normal(scale=1.0, size=(n_samples, n_features))
    return X, y


def run_config(rng, n_classes, n_features, n_samples, fit_intercept, n_cs, sep):
    """Drive the real patched helper in both modes; compare every recorded
    probability row against the shadow. Returns (rows_checked, err|None)."""
    from sklearn.linear_model.logistic import _log_reg_scoring_path

    X, y = make_data(rng, n_classes, n_features, n_samples, sep)
    n_train = int(0.7 * n_samples)
    train = np.arange(n_train)
    test = np.arange(n_train, n_samples)

    rows = 0
    for mode_str, mode_tag in (("multinomial", MULTINOMIAL), ("ovr", OVR)):
        records = []

        def recorder(est, X_test, y_test):
            real = est.predict_proba(X_test)
            shadow = scoring_estimator_proba(mode_tag, (est, X_test))
            records.append((np.asarray(real), np.asarray(shadow)))
            return 0.0

        kwargs = dict(scoring=recorder, fit_intercept=fit_intercept,
                      Cs=n_cs, multi_class=mode_str, solver="lbfgs",
                      max_iter=50)
        if mode_str == "ovr":
            kwargs["pos_class"] = int(np.unique(y)[0])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            _log_reg_scoring_path(X, y, train, test, **kwargs)

        if not records:
            return rows, "helper produced no scoring calls (mode tag %d)" % mode_tag
        for real, shadow in records:
            if real.shape != shadow.shape:
                return rows, ("DISAGREEMENT (shape) mode=%d real=%r shadow=%r"
                              % (mode_tag, real.shape, shadow.shape))
            if not np.allclose(shadow, real, rtol=1e-10, atol=1e-12):
                i = int(np.argmax(np.max(np.abs(shadow - real), axis=1)))
                return rows, ("DISAGREEMENT mode=%d sample_row=%d\n"
                              "  shadow=%r\n  real=%r"
                              % (mode_tag, i, shadow[i].tolist(),
                                 real[i].tolist()))
            rows += real.shape[0]
    return rows, None


def main():
    rng = np.random.RandomState(SEED)

    boundary = [
        # (n_classes, n_features, n_samples, fit_intercept, n_cs, sep)
        (3, 4, 200, False, 4, 2.0),    # the multiclass probabilistic shape
        (3, 4, 200, True, 4, 2.0),
        (2, 3, 150, False, 3, 2.0),    # binary boundary
        (2, 3, 150, True, 3, 2.0),
        (5, 6, 300, False, 4, 1.0),
        (4, 2, 200, True, 4, 5.0),     # strong separation (large decisions)
        (3, 8, 250, False, 5, 0.3),    # weak separation
        (3, 4, 60, True, 2, 2.0),      # small test fold
    ]

    checked = 0
    configs_run = 0
    for cfg in boundary:
        n, err = run_config(rng, *cfg)
        checked += n
        configs_run += 1
        if err:
            print("G-CONF FAIL (seed=%d) at config %r:" % (SEED, cfg))
            print(err)
            return 1

    while checked < TARGET_ROWS:
        cfg = (rng.randint(2, 6), rng.randint(2, 9),
               int(rng.randint(400, 1200)), bool(rng.randint(0, 2)),
               int(rng.randint(2, 8)), float(rng.uniform(0.3, 4.0)))
        n, err = run_config(rng, *cfg)
        checked += n
        configs_run += 1
        if err:
            print("G-CONF FAIL (seed=%d) at config %r:" % (SEED, cfg))
            print(err)
            return 1

    print("G-CONF OK: model.py impl shadow (real softmax / one-vs-rest "
          "transform callees) agrees with the real patched scoring "
          "estimator's probability output on %d probability rows across "
          "%d configurations x 2 modes (seed=%d), 0 disagreements."
          % (checked, configs_run, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
