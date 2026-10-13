#!/usr/bin/env python3
"""G-AX / deep-model soundness check for scikit-learn__scikit-learn-13496.

This bundle consumes NO `@ContractOnly` axiom: the reuse decision and the
roster update are modelled DEEPLY (the `refit_to_size` dispatch over
`reuse_and_extend` / `rebuild_all`, with the pure `fresh_run`). What must be
validated out-of-band is that this deep model agrees with the REAL incremental
roster behaviour of `sklearn.ensemble.IsolationForest` once the construction
option is exposed and carried through to fitting (the gold patch).

It runs the REAL post-patch estimator in-container and asserts, for both the
reuse and the rebuild cases, the exact structural predicates `model.py`'s
post-conditions encode:

  reuse-and-extend (caller opts in to reuse, members already present):
      * final size == requested total          (len(Result()) == target_count)
      * the existing members are preserved verbatim as the prefix — same
        identities, same order, same positions  (ToSeq(Result()) prefix ==
        ToSeq(existing)); in particular the first member survives
      * the appended tail are freshly-built members
        (ToSeq(Result()).drop(len(existing)) == fresh_run(...))

  rebuild (caller does not opt in):
      * final size == requested total
      * every member is freshly built — NO previously-present member survives
        (the first member is rebuilt, not preserved)

Member identity is the real Python object identity of each fitted sub-estimator,
tested with the `is` operator against RETAINED references to the prior objects
(exactly as the real F2P test does: `tree_1 = clf.estimators_[0]; ...;
clf.estimators_[0] is tree_1`). We deliberately do NOT compare bare `id()`
integers: when the cold-rebuild path frees the prior `ExtraTreeRegressor`
objects (`self.estimators_ = []`) before building fresh ones, CPython recycles
those memory addresses into the new objects, so `id()` would collide while the
objects are genuinely distinct — a false "survivor". Holding live references to
the prior objects (and using `is`) makes the freshness test sound. A
"freshly-built" member is one that is not (by `is`) any of the retained prior
members. This is exactly the abstraction `model.py` uses (non-negative
identities for already-present members, the FRESH_MEMBER sentinel for
freshly-built ones).

Imports only `numpy` and `sklearn` (the library under change), nothing
repo-private. Exit 0 iff every observation matches the model.
"""
import sys
import warnings

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.utils import check_random_state


def _fit_objs(clf, X):
    """Fit `clf` on `X` and return the roster as a list of the actual fitted
    sub-estimator OBJECTS (live references), mirroring model.py's roster of
    member identities. Returning the objects themselves (rather than their
    `id()`) keeps them alive, so CPython cannot recycle a freed object's address
    into a freshly-built one; freshness is then tested by `is` (true object
    identity), exactly like the F2P test."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        clf.fit(X)
    return list(clf.estimators_)


def check_reuse_and_extend(n_first, n_total, seed):
    """REAL warm-start refit: opt in to reuse, fit n_first, then enlarge to
    n_total and fit again. Assert the model's reuse-and-extend postconditions:
    size == n_total, existing members preserved verbatim as the prefix, tail
    freshly built."""
    rng = check_random_state(seed)
    X = rng.randn(20, 2)
    clf = IsolationForest(n_estimators=n_first, max_samples=20,
                          random_state=rng, warm_start=True)
    existing = _fit_objs(clf, X)  # retained live references
    assert len(existing) == n_first, (
        "setup: expected %d members, got %d" % (n_first, len(existing)))

    clf.set_params(n_estimators=n_total)
    result = _fit_objs(clf, X)  # retained live references

    # final size == requested total
    assert len(result) == n_total, (
        "reuse: len(result)=%d != target_count=%d" % (len(result), n_total))
    # existing members preserved verbatim as the prefix (same OBJECTS, same
    # order, same positions) -> in particular result[0] is existing[0]
    for k in range(len(existing)):
        assert result[k] is existing[k], (
            "reuse: existing prefix NOT preserved at position %d "
            "(result[%d] is not existing[%d])" % (k, k, k))
    # the appended tail are freshly-built members (not, by `is`, any object
    # present before the refit)
    tail = result[len(existing):]
    assert len(tail) == n_total - n_first
    for obj in tail:
        for e in existing:
            assert obj is not e, (
                "reuse: an appended member is a prior object (not fresh)")


def check_rebuild(n_first, n_total, seed):
    """REAL cold refit: do NOT opt in to reuse (default warm_start=False), fit
    n_first, then enlarge to n_total and fit again. Assert the model's rebuild
    postconditions: size == n_total, every member freshly built (no previously-
    present member survives — the first member is rebuilt)."""
    rng = check_random_state(seed)
    X = rng.randn(20, 2)
    clf = IsolationForest(n_estimators=n_first, max_samples=20,
                          random_state=rng)  # warm_start defaults to False
    existing = _fit_objs(clf, X)  # retained live references (prevent id reuse)
    assert len(existing) == n_first

    clf.set_params(n_estimators=n_total)
    result = _fit_objs(clf, X)  # retained live references

    assert len(result) == n_total, (
        "rebuild: len(result)=%d != target_count=%d" % (len(result), n_total))
    # every member is freshly built: none of the previously-present member
    # OBJECTS survives (the whole forest was rebuilt). Tested by `is` against
    # the retained prior objects, so a recycled address cannot masquerade as a
    # survivor.
    for obj in result:
        for e in existing:
            assert obj is not e, (
                "rebuild: a prior member object survived the rebuild "
                "(should be fresh)")
    # keep `existing` alive through the identity comparisons above
    assert len(existing) == n_first


def main():
    # boundary + small fuzz over (n_first, n_total) with n_first <= n_total
    cases = [
        (10, 20),   # the F2P scenario: 10 then 20
        (1, 2),
        (1, 10),
        (5, 5),     # n_total == n_first (no new trees; prefix still preserved)
        (3, 4),
        (7, 13),
        (2, 25),
    ]
    seeds = [0, 1, 2, 7, 42]
    for seed in seeds:
        for (a, b) in cases:
            check_reuse_and_extend(a, b, seed)
            check_rebuild(a, b, seed)

    print("G-AX OK: deep model (reuse-and-extend / rebuild over fresh_run) "
          "matches the real IsolationForest incremental-roster behaviour on "
          "%d (reuse + rebuild) scenarios" % (len(seeds) * len(cases) * 2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
