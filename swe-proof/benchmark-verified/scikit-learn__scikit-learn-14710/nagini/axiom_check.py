#!/usr/bin/env python3
"""G-AX executable soundness check for scikit-learn__scikit-learn-14710.

The bundle consumes NO @ContractOnly axiom. Its one kind-A obligation is an
A-reference: the deep model of the changed operation — the per-element gather
`decode_one(labels, t[i]) == labels[t[i]]` (model.py `pure` region), assembled
into `Result()[i] == labels[target[i]]` — must equal the REAL operation the
gold patch performs:

    y_decoded = self.classes_[y_encoded.astype(int)]

i.e. numpy fancy-indexing of the LabelEncoder class table by the internal
integer target indices. This script runs that real operation (numpy + the real
sklearn LabelEncoder) on boundary + fuzz inputs and asserts:

  (1) the real gather `classes_[indices]` agrees element-wise with the model's
      `decode_one` over the same (labels, indices) — the A-reference check; and
  (2) the encode/decode round trip is the identity: for targets produced by the
      real LabelEncoder, `classes_[encoded] == original_y` — which is exactly
      why the decode places the scored target in the same representation as the
      estimator's predictions (the behaviour the spec pins).

Exit 0 iff every observation holds.
"""
import random
import sys

import numpy as np
from sklearn.preprocessing import LabelEncoder


# --- model.py reference encodings (kept in lock-step with the pure region) ---

def decode_one(labels, x):
    """Reference of model.py's `decode_one`: labels[x] for a valid index x."""
    if 0 <= x < len(labels):
        return labels[x]
    return x


def model_decoded(labels, indices):
    """Reference of the contracted result: element i is decode_one(labels, t[i])."""
    return [decode_one(labels, int(t)) for t in indices]


# --- the checks --------------------------------------------------------------

def check_gather_reference(labels, indices):
    """(1) The deep-model gather == the REAL numpy fancy-index classes_[t]."""
    classes_ = np.asarray(labels)
    real = list(classes_[np.asarray(indices).astype(int)])          # real callee
    expected = model_decoded(list(labels), indices)                 # deep model
    assert list(real) == list(expected), (
        "decode_one deep model unsound: labels=%r indices=%r real=%r model=%r"
        % (labels, indices, real, expected))


def check_round_trip(y):
    """(2) For real LabelEncoder output, classes_[encoded] == original y, and the
    model decode reproduces it. This is the representation-consistency property
    the spec pins (the scorer receives original-domain labels)."""
    le = LabelEncoder()
    encoded = le.fit_transform(y)                                   # real callee
    classes_ = le.classes_                                          # real table
    # The standing precondition the spec requires (in_index_range):
    assert all(0 <= int(t) < len(classes_) for t in encoded)
    decoded_real = classes_[encoded.astype(int)]                    # real gather
    assert list(decoded_real) == list(y), (
        "round trip broken: y=%r encoded=%r decoded=%r"
        % (list(y), list(encoded), list(decoded_real)))
    # And the deep model reproduces the same gather on the integer carrier.
    labels_int = list(range(len(classes_)))   # abstract original labels as ints
    # map original y-values to their integer abstraction via the same ordering
    value_to_int = {v: i for i, v in enumerate(classes_)}
    model_labels = [value_to_int[v] for v in classes_]              # = [0..k-1]
    model_out = model_decoded(model_labels, list(encoded))
    expected_int = [value_to_int[v] for v in decoded_real]
    assert model_out == expected_int, (
        "deep model disagrees with real gather under int abstraction: "
        "y=%r model=%r expected=%r" % (list(y), model_out, expected_int))


def main():
    rng = random.Random(14710)

    # --- (1) boundary gather cases ---------------------------------------
    # labels are the (abstracted-as-int) class table; indices are internal
    # target indices, always in 0..len(labels)-1 (the spec's precondition).
    boundary = [
        ([10], [0, 0, 0]),
        ([10, 20], [0, 1, 1, 0]),
        ([5, 6, 7], [2, 1, 0, 2, 0]),
        ([100, 200, 300, 400], [3, 2, 1, 0]),
        ([0, 1], []),                       # empty target
        ([42], [0]),                        # singleton everywhere
    ]
    for labels, indices in boundary:
        check_gather_reference(labels, indices)

    # --- (1) fuzz gather --------------------------------------------------
    for _ in range(20000):
        k = rng.randint(1, 8)
        labels = rng.sample(range(-1000, 1000), k)
        n = rng.randint(0, 30)
        indices = [rng.randint(0, k - 1) for _ in range(n)]
        check_gather_reference(labels, indices)

    # --- (2) round trip over real LabelEncoder, incl. STRING targets ------
    string_targets = [
        np.array(['x'] * 50 + ['y'] * 50, dtype=object),   # the issue's case
        np.array(['x', 'y', 'x', 'y', 'x'], dtype=object),
        np.array(['cat', 'dog', 'cat', 'bird', 'dog', 'cat'], dtype=object),
        np.array(['b', 'a', 'c', 'a', 'b', 'c', 'a'], dtype=object),
        np.array(['only'] * 7, dtype=object),
        np.array([1.0, 2.0, 1.0, 3.0, 2.0]),               # numeric labels
        np.array([0, 1, 0, 2, 1, 2]),
    ]
    for y in string_targets:
        check_round_trip(y)

    # fuzz round trips with random string class sets
    pool = ['x', 'y', 'z', 'cat', 'dog', 'alpha', 'beta', 'q', 'foo', 'bar']
    for _ in range(2000):
        kc = rng.randint(2, 6)
        classes = rng.sample(pool, kc)
        n = rng.randint(kc, 40)
        y = np.array([rng.choice(classes) for _ in range(n)], dtype=object)
        check_round_trip(y)

    print("G-AX OK: decode_one deep model == real numpy classes_[t] gather over "
          "%d boundary + 20000 fuzz gathers, and LabelEncoder encode/decode "
          "round trip is the identity over string + numeric targets."
          % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
