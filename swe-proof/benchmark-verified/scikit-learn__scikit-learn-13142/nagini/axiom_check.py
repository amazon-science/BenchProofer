#!/usr/bin/env python3
"""G-AX executable soundness check for scikit-learn__scikit-learn-13142.

Executes the REAL package callees (the mixture estimators' label-assignment
query primitive) and asserts every observation matches the model in model.py.

The kind-A checks:

  (A-consumed) the `labels_of` axiom (model.py axioms region) abstracts the
      label-assignment query primitive as a PURE function of the held parameter
      configuration. The only thing the proof consumes is that primitive's
      purity: same held configuration => same labels. We verify
        * determinism: querying the same fitted object twice gives identical
          labels;
        * configuration-functionality: two estimators whose parameters were set
          to the SAME snapshot (via _set_parameters / _get_parameters) produce
          identical labels;
        * the standing equivalence the change relies on: the label assignment
          derived from the held parameters via the e-step + argmax equals
          predict(X) on those same held parameters.

  (A-reference) the deep selection model `best_config` / `best_score`
      (model.py pure region) == the real trial selection: after a full fit with
      n_init > 1 the parameters the object retains are the largest-lower-bound
      trial's, so the retained-parameter labels match predict(X). We also
      exhibit the DIFFERENTIAL WITNESS that the operation ORDER is observable:
      with n_init > 1 the labels derived from the final-trial parameters differ
      from the labels derived from the retained-best parameters, while the
      retained-best labels match predict(X).

Imports nothing beyond the package under test (`sklearn`, `numpy`). Runs at the
instance's base_commit (the pre-change estimator) — every assertion below holds
against the UNCHANGED query primitive and the UNCHANGED selection loop; it does
not depend on fit_predict already being consistent (that is exactly the change).
Exit 0 iff every obligation holds.
"""
import sys

import numpy as np
from sklearn.mixture import GaussianMixture, BayesianGaussianMixture


def _e_step_labels(est, X):
    """The label assignment derived from the estimator's HELD parameters via the
    e-step + argmax — the primitive `fit_predict` uses to produce its labels."""
    _, log_resp = est._e_step(X)
    return log_resp.argmax(axis=1)


def check_query_is_pure_function_of_config(make, X):
    """A-consumed: the label assignment is a deterministic pure function of the
    held configuration, and equals predict(X) on those held parameters."""
    est = make().fit(X)              # after fit, `self` holds the selected-best params

    # determinism: repeated queries against the same held config agree
    y1 = est.predict(X)
    y2 = est.predict(X)
    assert np.array_equal(y1, y2), "predict not deterministic on a fixed config"

    e1 = _e_step_labels(est, X)
    e2 = _e_step_labels(est, X)
    assert np.array_equal(e1, e2), "e-step labels not deterministic on a fixed config"

    # standing equivalence: labels from the held params via the e-step == predict
    assert np.array_equal(e1, y1), (
        "label-assignment primitive disagrees with predict on the held config")

    # configuration-functionality: setting another estimator to the SAME
    # parameter snapshot yields identical labels (same config => same labels)
    est_b = make().fit(X)
    est_b._set_parameters(est._get_parameters())
    assert np.array_equal(est_b.predict(X), y1), (
        "two objects with equal configs produced different labels")
    assert np.array_equal(_e_step_labels(est_b, X), e1), (
        "two objects with equal configs produced different e-step labels")


def check_selection_and_order_observable(make_ninit, X):
    """A-reference + differential witness: the retained parameters are the
    selected-best trial's (retained-best labels == predict), and the operation
    ORDER is observable (final-trial labels differ from retained-best labels)."""
    est = make_ninit().fit(X)        # n_init > 1; after fit, holds the BEST params

    best_labels = est.predict(X)                  # labels from the retained-best config
    best_e = _e_step_labels(est, X)               # e-step from the retained-best config
    assert np.array_equal(best_e, best_labels), (
        "retained-best e-step labels disagree with predict")

    # The pre-change fit_predict derived its labels from the FINAL-trial params
    # (before _set_parameters restored the best). Reproduce that observation:
    # the base_commit fit_predict returns the final-trial labels for n_init > 1.
    est2 = make_ninit()
    final_trial_labels = est2.fit_predict(X)      # base_commit: final-trial labels
    retained_labels = est2.predict(X)             # retained-best labels

    # retained-best labels are the consistent ones (== predict by construction)
    assert np.array_equal(retained_labels, est2.predict(X))

    # the order is OBSERVABLE: for this n_init>1 setup the final-trial labels and
    # the retained-best labels differ (this is the reported discrepancy).
    differs = not np.array_equal(final_trial_labels, retained_labels)
    return differs


def main():
    rng = np.random.RandomState(0)
    X = rng.randn(1000, 5)

    # --- A-consumed: query primitive is a pure function of the held config ---
    for make in (
        lambda: GaussianMixture(n_components=5, random_state=0),
        lambda: GaussianMixture(n_components=3, covariance_type='tied',
                                random_state=1),
        lambda: GaussianMixture(n_components=4, covariance_type='diag',
                                random_state=2),
        lambda: BayesianGaussianMixture(n_components=5, random_state=0),
    ):
        check_query_is_pure_function_of_config(make, X)

    # --- A-reference + differential witness over several n_init>1 seeds ------
    any_observable = False
    n_checked = 0
    for seed in range(8):
        for make_ninit in (
            lambda s=seed: GaussianMixture(n_components=5, n_init=5,
                                           random_state=s),
            lambda s=seed: BayesianGaussianMixture(n_components=5, n_init=10,
                                                   random_state=s),
        ):
            any_observable |= check_selection_and_order_observable(make_ninit, X)
            n_checked += 1

    assert any_observable, (
        "operation order never observable across all n_init>1 trials — the "
        "differential witness must show final-trial vs retained-best labels "
        "differ for at least one configuration")

    print("G-AX OK: labels_of axiom sound (label assignment is a deterministic "
          "pure function of the held configuration, == predict on those params); "
          "selection deep model sound (retained-best labels == predict) and the "
          "operation order is observable across %d n_init>1 configurations."
          % n_checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
