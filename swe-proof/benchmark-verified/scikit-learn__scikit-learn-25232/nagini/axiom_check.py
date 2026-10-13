#!/usr/bin/env python3
"""G-AX executable soundness check for scikit-learn__scikit-learn-25232.

Executes the REAL unchanged callee (the single-pass imputer's constant
strategy) on numerical data and asserts every observation matches the
`constant_statistics` axiom in model.py:

  (A-consumed) constant_statistics(requested, n_features):
      len(result) == n_features and, for every feature j,
        result[j] == resolved_value(requested)
      where resolved_value(None) == 0 and resolved_value(v) == v.
      This is exactly the per-feature constant array a single-pass imputer
      installs under strategy="constant": np.full(n_features, fill_value)
      after fill_value defaults to 0 for numerical data when None.

It also validates, end-to-end, that the iterative imputer's first-round
constant initialization carries the user-requested replacement value through
to that callee (the A-reference for the modelled propagation), reproducing the
discriminating FAIL_TO_PASS observation (fill_value=100 -> statistics_ == 100,
not 0).

Imports only the public scikit-learn API (the package under test) and numpy.
Exit 0 iff every obligation holds.
"""
import sys

import numpy as np
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer, SimpleImputer


def resolved_value(requested):
    """model.py's resolved_value: supplied value, else neutral default 0."""
    return 0 if requested is None else requested


def check_constant_statistics_axiom(requested, n_features):
    """Assert the REAL SimpleImputer(strategy='constant') installs, for every
    feature, the (default-resolved) requested value — the constant_statistics
    axiom Ensures."""
    # numerical data, n_features columns, a few rows with missing entries.
    rng = np.random.RandomState(25232)
    X = rng.randint(-5, 5, size=(6, n_features)).astype(float)
    # inject the sentinel missing value (-1) so there is something to fill
    X[0, :] = -1
    kwargs = {"missing_values": -1, "strategy": "constant"}
    if requested is not None:
        kwargs["fill_value"] = requested
    imp = SimpleImputer(**kwargs)
    imp.fit(X)
    stats = imp.statistics_
    expected = resolved_value(requested)
    assert stats.shape[0] == n_features, (
        "constant_statistics axiom unsound: len(statistics_)=%d, n_features=%d"
        % (stats.shape[0], n_features))
    for j in range(n_features):
        assert stats[j] == expected, (
            "constant_statistics axiom unsound on requested=%r feature %d: "
            "statistics_[j]=%r, axiom requires %r"
            % (requested, j, stats[j], expected))


def check_iterative_propagation(requested):
    """A-reference: the iterative imputer carries the user-requested
    replacement value through to its first-round constant initializer; every
    installed per-feature constant equals the (default-resolved) value. This is
    the discriminating FAIL_TO_PASS observation."""
    X = np.array(
        [[-1, 2, 3, -1], [4, -1, 5, -1], [6, 7, -1, -1], [8, 9, 0, -1]],
        dtype=float,
    )
    kwargs = {"missing_values": -1, "initial_strategy": "constant", "max_iter": 0}
    if requested is not None:
        kwargs["fill_value"] = requested
    imp = IterativeImputer(**kwargs)
    imp.fit_transform(X)
    stats = imp.initial_imputer_.statistics_
    expected = resolved_value(requested)
    for j in range(stats.shape[0]):
        assert stats[j] == expected, (
            "iterative-imputer propagation unsound on fill_value=%r feature %d:"
            " statistics_[j]=%r, expected %r"
            % (requested, j, stats[j], expected))


def main():
    # constant_statistics axiom: boundary + fuzz over requested values and
    # feature counts.
    requested_values = [None, 0, 1, -1, 100, -100, 7, 42, 999, -3]
    feature_counts = [1, 2, 3, 4, 8, 16]
    for req in requested_values:
        for n in feature_counts:
            check_constant_statistics_axiom(req, n)

    # end-to-end propagation (A-reference), incl. the F2P fill_value=100 case.
    for req in [None, 0, 1, 100, -1, 50]:
        check_iterative_propagation(req)

    n_checks = len(requested_values) * len(feature_counts)
    print(
        "G-AX OK: constant_statistics axiom sound on %d (requested x n_features)"
        " observations; iterative-imputer propagation sound incl. fill_value=100"
        % n_checks
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
