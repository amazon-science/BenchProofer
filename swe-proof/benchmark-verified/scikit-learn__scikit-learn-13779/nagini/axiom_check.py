#!/usr/bin/env python3
"""G-AX executable soundness check for scikit-learn__scikit-learn-13779.

Executes the REAL capability probe the changed code invokes —
`sklearn.utils.validation.has_fit_parameter(estimator, 'sample_weight')` (the
unchanged callee at sklearn/ensemble/voting.py:81) — against the
`accepts_weighting` axiom encoded in model.py:

    Requires(status == 1 or status == 2)        # PRESENT entries only
    Ensures(Result() == (status == 1))           # accepts weighting iff status 1

The status -> reality mapping (mapping.md §2):
    status 1 (present, accepts) -> a real estimator whose `fit` declares
        `sample_weight`; has_fit_parameter must return True.
    status 2 (present, rejects) -> a real estimator whose `fit` does NOT declare
        `sample_weight`; has_fit_parameter must return False.
    status 0 (absent) is OUTSIDE the axiom's precondition: the probe is never
        consulted on an absent entry. Soundness of that precondition is the
        crux of the bug — the REAL probe RAISES when applied to an absent entry
        (`None.fit` -> AttributeError), so admitting status 0 to the probe would
        be unsound. This check confirms the probe genuinely raises on None, i.e.
        the precondition that excludes status 0 is not a fabricated restriction.

Imports the very callee the patch's surrounding code calls
(`sklearn.utils.validation.has_fit_parameter`) plus real sklearn estimators;
both are present in the evaluation container. Exit 0 iff every obligation holds.
"""
import random
import sys

from sklearn.utils.validation import has_fit_parameter  # the REAL probe

# Real estimators whose `fit` signature DOES declare `sample_weight`
# (status 1: present-and-accepts).
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.svm import SVC

# A real estimator whose `fit` signature DOES declare `sample_weight`
# (status 1: GaussianNB.fit is `fit(self, X, y, sample_weight=None)` at
# sklearn/naive_bayes.py:167).
from sklearn.naive_bayes import GaussianNB

# A real estimator whose `fit` signature does NOT declare `sample_weight`
# (status 2: KNeighborsClassifier.fit is `fit(self, X, y)` at
# sklearn/neighbors/base.py:878).
from sklearn.neighbors import KNeighborsClassifier


class _NoWeightEstimator:
    """A minimal present sub-estimator whose `fit` does NOT accept
    `sample_weight` (status 2)."""
    def fit(self, X, y):
        return self


class _WeightEstimator:
    """A minimal present sub-estimator whose `fit` DOES accept
    `sample_weight` (status 1)."""
    def fit(self, X, y, sample_weight=None):
        return self


def check_present(estimator, expected_accepts):
    """Assert has_fit_parameter(estimator, 'sample_weight') == expected_accepts,
    i.e. the axiom's Ensures(Result() == (status == 1)) holds for this present
    entry."""
    observed = has_fit_parameter(estimator, 'sample_weight')   # REAL probe
    assert isinstance(observed, bool), (
        "accepts_weighting axiom UNSOUND: real probe returned non-bool %r on %r"
        % (observed, type(estimator).__name__))
    assert observed == expected_accepts, (
        "accepts_weighting axiom UNSOUND on %s: real has_fit_parameter gave %r, "
        "axiom requires %r (status %d)"
        % (type(estimator).__name__, observed, expected_accepts,
           1 if expected_accepts else 2))


def main():
    # ---- status 1: present estimators that ACCEPT sample weighting -----------
    accepts = [
        LogisticRegression(), LinearRegression(),
        RandomForestClassifier(n_estimators=2), RandomForestRegressor(n_estimators=2),
        DecisionTreeClassifier(), DecisionTreeRegressor(),
        SVC(), GaussianNB(), _WeightEstimator(),
    ]
    for est in accepts:
        check_present(est, True)

    # ---- status 2: present estimators that REJECT sample weighting -----------
    rejects = [
        KNeighborsClassifier(), _NoWeightEstimator(),
    ]
    for est in rejects:
        check_present(est, False)

    # ---- status 0 (absent): the probe is OUTSIDE its precondition ------------
    # The axiom admits only present statuses {1, 2}; status 0 (an absent entry,
    # i.e. None) is excluded. Soundness of that exclusion: the REAL probe RAISES
    # when applied to an absent entry, so it genuinely cannot be consulted there
    # (this is the bug the fix avoids by skipping absent entries). Confirm the
    # raise so the precondition is shown to be a faithful restriction, not an
    # arbitrary one.
    raised = False
    try:
        has_fit_parameter(None, 'sample_weight')   # REAL probe on an absent entry
    except AttributeError:
        raised = True
    except Exception:
        # any raise confirms the probe cannot be consulted on an absent entry;
        # AttributeError ('NoneType' object has no attribute 'fit') is the
        # observed one, matching the issue.
        raised = True
    assert raised, (
        "accepts_weighting precondition UNSOUND: real has_fit_parameter(None, "
        "'sample_weight') did NOT raise; status 0 would then be admissible and "
        "the precondition status in {1,2} would be an over-restriction")

    # ---- fuzz: synthesized estimators with/without a sample_weight kwarg -----
    rng = random.Random(13779)
    for _ in range(2000):
        if rng.random() < 0.5:
            est = _WeightEstimator()
            check_present(est, True)
        else:
            est = _NoWeightEstimator()
            check_present(est, False)

    print("G-AX OK: accepts_weighting axiom sound against the real "
          "has_fit_parameter probe on %d weight-accepting + %d weight-rejecting "
          "present estimators + 2000 fuzz; and the real probe RAISES on an "
          "absent entry (None), confirming the precondition status in {1,2} is a "
          "faithful restriction (the bug the fix avoids)."
          % (len(accepts), len(rejects)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
