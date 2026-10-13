"""G-AX executable soundness check for scikit-learn__scikit-learn-14629.

There is NO @ContractOnly axiom in model.py (the gathering of per-output class
labels is modelled deeply, and the unchanged fitting step is taken as a typed
input rather than re-derived). So this script validates the *behavioural claim*
the spec's postconditions encode, against the REAL patched code, in-container:

  After fitting a MultiOutputClassifier, ``self.classes_`` must be

    (1) a Python ``list``                              -> isinstance(..., list)
    (2) of length == number of fitted sub-estimators   -> len matches len(estimators_)
    (3) whose entry i is element-for-element VALUE-     -> np.array_equal
        equal to the class-label array of sub-estimator i

These mirror exactly the model.py postconditions
``Acc(list_pred(Result()))`` / ``len(Result()) == len(estimators)`` /
``Forall k: Result()[k] == est_vals(estimators[k])`` under the type refinement
in refinement.md (R rows A1/A3/A4/A5). Check (3) uses VALUE equality
(``np.array_equal``), exactly the discriminator the F2P test observes
(``assert_array_equal``) and the only property the spec pins — NOT object
identity, which no test or consumer here observes.

stdlib + the patched module's hard dependencies only (sklearn, numpy). Exit 0
iff every observation is sound; non-zero on the first violation. Must be run in
the patched (post-gold) container — pre-patch it raises AttributeError, which
this script reports as the bug it guards against.
"""
import sys

import numpy as np
from sklearn.multioutput import MultiOutputClassifier
from sklearn.ensemble import RandomForestClassifier


def check_one(n_outputs, n_classes_per_output, n_samples, seed):
    rng = np.random.RandomState(seed)
    X = rng.randn(n_samples, 5)
    # Build a target matrix with `n_outputs` columns; column j has
    # `n_classes_per_output[j]` distinct labels (and every label is present so
    # the fitted sub-estimator's classes_ is exactly those labels).
    cols = []
    expected_labels = []
    for j in range(n_outputs):
        k = n_classes_per_output[j]
        # guarantee each of the k labels appears at least once
        base = np.arange(n_samples) % k
        rng.shuffle(base)
        cols.append(base)
        expected_labels.append(np.unique(base))
    Y = np.column_stack(cols)

    clf = MultiOutputClassifier(RandomForestClassifier(n_estimators=2,
                                                       random_state=seed))
    clf.fit(X, Y)

    # (1) classes_ is a list
    if not isinstance(clf.classes_, list):
        print("VIOLATION (1): classes_ is %r, not a list (seed=%d)"
              % (type(clf.classes_), seed))
        return False

    # (2) one entry per fitted sub-estimator (== n_outputs)
    if len(clf.classes_) != len(clf.estimators_):
        print("VIOLATION (2): len(classes_)=%d != len(estimators_)=%d (seed=%d)"
              % (len(clf.classes_), len(clf.estimators_), seed))
        return False
    if len(clf.classes_) != n_outputs:
        print("VIOLATION (2): len(classes_)=%d != n_outputs=%d (seed=%d)"
              % (len(clf.classes_), n_outputs, seed))
        return False

    # (3) entry i is element-for-element VALUE-equal to estimators_[i].classes_
    #     (the model's `Result()[i] == est_vals(estimators[i])`), the property
    #     the F2P test observes via assert_array_equal.
    for i, est in enumerate(clf.estimators_):
        if not np.array_equal(clf.classes_[i], est.classes_):
            print("VIOLATION (3): classes_[%d] != estimators_[%d].classes_ "
                  "by value (seed=%d)" % (i, i, seed))
            return False
        # the per-output label values are exactly the genuine learned labels.
        if not np.array_equal(clf.classes_[i], expected_labels[i]):
            print("VIOLATION (3b): classes_[%d]=%r != expected %r (seed=%d)"
                  % (i, clf.classes_[i], expected_labels[i], seed))
            return False

    return True


def main():
    cases = []
    # boundary: a single output
    cases.append((1, [2], 30, 0))
    cases.append((1, [3], 40, 1))
    # the F2P shape: 3 outputs, 3 classes each (iris-like)
    cases.append((3, [3, 3, 3], 60, 2))
    # heterogeneous class counts across outputs
    cases.append((4, [2, 3, 4, 5], 80, 3))
    cases.append((2, [2, 2], 20, 4))
    # fuzz: random output counts / class counts / sizes
    rng = np.random.RandomState(12345)
    for s in range(40):
        n_out = int(rng.randint(1, 6))
        per = [int(rng.randint(2, 6)) for _ in range(n_out)]
        n_samp = int(max(per) * rng.randint(4, 12))
        cases.append((n_out, per, n_samp, 1000 + s))

    ok = 0
    for (n_out, per, n_samp, seed) in cases:
        if not check_one(n_out, per, n_samp, seed):
            print("axiom_check FAILED on case n_out=%d per=%r n_samp=%d seed=%d"
                  % (n_out, per, n_samp, seed))
            sys.exit(1)
        ok += 1

    print("axiom_check OK: behavioural claim sound on %d cases "
          "(classes_ is a list, one entry per sub-estimator, "
          "entry i is value-equal to estimators_[i].classes_)." % ok)
    sys.exit(0)


if __name__ == "__main__":
    main()
