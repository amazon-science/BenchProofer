#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-14629
(plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated to
              Python over the real repo types (mapping.md §2): the backward fold
              `gatheredLabels submodels` ↔ the per-sub-model expansion, observed
              as the list of per-sub-model label collections, in order. No callee
              is A-substituted in the impl loop body (A1 is a consumed
              precondition, not an op), so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the added assignment
              `[estimator.classes_ for estimator in self.estimators_]`.

Two legs:
  1. SYNTHETIC (≥10^5): fuzz `estimators_` as lists of mock sub-models, each with
     a random integer `.classes_` array. shadow = [s.labels-modeled]; oracle =
     the patch comprehension applied to the same mocks. Observable = the list of
     label collections, in order, plus length == n_outputs. Exercises every list
     length / element / order combination the bijection must preserve.
  2. GROUNDING: real `MultiOutputClassifier(RandomForestClassifier(...))` fitted
     on fuzzed multilabel data — assert the patched `clf.classes_` equals
     `[e.classes_ for e in clf.estimators_]` (deep array equality), is a list,
     and has length n_outputs (the F2P observations).

Runs in-container; stdlib + repo. Seed pinned (mapping.md §4). Exit 0 iff zero
disagreements; any disagreement is an R/I-fidelity counterexample.
"""
import random
import sys

SEED = 14629
N_FUZZ = 100_000


class _MockSub:
    """A mock sub-model carrying only the touched field, `.classes_` — the
    Lean `Submodel.labels` (mapping.md §2)."""
    def __init__(self, classes):
        self.classes_ = list(classes)


def shadow_gather(submodels):
    """`gatheredLabels submodels` transliterated: one label collection per
    sub-model, in order (the backward fold's R/I observable)."""
    result = []
    i = len(submodels)
    while i > 0:
        s = submodels[i - 1]
        result = [s.classes_] + result
        i -= 1
    return result


def oracle_gather(submodels):
    """patch.diff's behaviour: the added comprehension
    `[estimator.classes_ for estimator in self.estimators_]`."""
    return [estimator.classes_ for estimator in submodels]


def synthetic_leg():
    rng = random.Random(SEED)
    disagreements = []
    for n in range(N_FUZZ):
        n_outputs = rng.randint(0, 6)
        submodels = []
        for _ in range(n_outputs):
            k = rng.randint(1, 5)
            classes = sorted(rng.sample(range(-20, 20), k))
            submodels.append(_MockSub(classes))

        shadow = shadow_gather(submodels)
        oracle = oracle_gather(submodels)
        if shadow != oracle:
            disagreements.append(("value", n, shadow, oracle))
        elif len(shadow) != n_outputs:
            disagreements.append(("length", n, len(shadow), n_outputs))
        if len(disagreements) >= 5:
            break
    return disagreements


def grounding_leg():
    try:
        import numpy as np
        from numpy.testing import assert_array_equal
        from sklearn.multioutput import MultiOutputClassifier
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.datasets import make_multilabel_classification
    except Exception as e:  # pragma: no cover
        return [("import", repr(e))]

    fails = []
    for seed in range(6):
        X, Y = make_multilabel_classification(
            n_samples=60, n_classes=3 + (seed % 4), n_labels=2,
            random_state=seed)
        n_outputs = Y.shape[1]
        clf = MultiOutputClassifier(
            RandomForestClassifier(n_estimators=2, random_state=seed))
        clf.fit(X, Y)
        if not isinstance(clf.classes_, list):
            fails.append(("not-list", seed, type(clf.classes_)))
            continue
        if len(clf.classes_) != n_outputs:
            fails.append(("len", seed, len(clf.classes_), n_outputs))
            continue
        expected = [e.classes_ for e in clf.estimators_]
        try:
            for got, exp in zip(clf.classes_, expected):
                assert_array_equal(got, exp)
        except AssertionError as e:
            fails.append(("array-neq", seed, repr(e)))
    return fails


def main():
    syn = synthetic_leg()
    if syn:
        print("G-CONF FAIL: %d synthetic R/I disagreement(s):" % len(syn))
        for d in syn:
            print("  %r" % (d,))
        return 1
    print("G-CONF: synthetic leg OK -- shadow gatheredLabels == "
          "[e.classes_ for e in estimators_] on %d fuzzed inputs (seed=%d)."
          % (N_FUZZ, SEED))

    grd = grounding_leg()
    if grd:
        print("G-CONF FAIL: %d grounding disagreement(s):" % len(grd))
        for d in grd:
            print("  %r" % (d,))
        return 1
    print("G-CONF OK: grounding leg -- real patched MultiOutputClassifier."
          "classes_ == [e.classes_ for e in estimators_] (deep array eq), is a "
          "list of length n_outputs. R/I shadow agrees with patch.diff.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
