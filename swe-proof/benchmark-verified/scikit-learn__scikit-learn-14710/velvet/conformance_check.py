#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-14710
(plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's `prepareScorerTargets` impl
              region transliterated to Python over the *real* repo carriers.
              The impl branches on the task kind (`isClf`); the classification
              arm returns the per-code lookup `gather labels y`
              (= `[labels[int(c)] for c in y]`, the element-wise map), and the
              regression arm returns `y` unchanged. There is NO axiomatized
              callee in this bundle — `gather` is an ordinary total table lookup,
              so the shadow is pure R/I (mapping.md §3).
  * ORACLE  — `patch.diff`'s behaviour: the real post-patch expression. On a
              classification task the scorer target becomes
              `self.classes_[y.astype(int)]` (NumPy advanced indexing); on a
              regression task the target is passed through unchanged. We exercise
              the REAL `classes_[y.astype(int)]` with NumPy in-process — it is
              exactly the Python the gold patch ships and needs neither a fitted
              sklearn estimator nor a DB nor Docker.

They must agree on every input: the shadow's prepared targets must equal the
oracle's prepared targets, on both the classifier and the regressor leg. Exit 0
iff zero disagreements; any disagreement is a mechanical R/I-fidelity
counterexample.

stdlib + numpy only (numpy is present in the SWE-Bench instance image, and is
the library the gold patch's `.astype(int)` / fancy index use). The fuzz seed is
pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

import numpy as np

SEED = 14710
N_FUZZ = 100_000


# --- SHADOW: Solution.lean prepareScorerTargets, transliterated --------------
# gather labels y = y.map (fun i => labels[i.toNat]!)   -- per-code index lookup
def shadow_gather(labels, y_codes):
    """The deep model `gather`: look each integer code up in the label table,
    in order (order- and count-preserving)."""
    return [labels[int(c)] for c in y_codes]


def shadow_prepare(is_clf, labels, y_codes):
    """prepareScorerTargets: classifier -> gather; regressor -> y unchanged."""
    if is_clf:
        return shadow_gather(labels, y_codes)
    else:
        return list(y_codes)


# --- ORACLE: patch.diff's behaviour, the real NumPy fancy index --------------
def oracle_prepare(is_clf, classes_, y_arr):
    """The patched scorer-target preparation:

        if is_classifier(self):
            y = self.classes_[y.astype(int)]

    `classes_` is the LabelEncoder.classes_ table; `y` is the integer-code
    target array (Y_DTYPE floats holding integer codes). For a regressor nothing
    is inserted and `y` reaches the scorer unchanged. This is the actual Python
    the gold patch ships; it needs neither sklearn nor a DB."""
    if is_clf:
        out = classes_[y_arr.astype(int)]
        return list(out)
    else:
        return list(y_arr)


def fuzz_cases(n, rng):
    # boundary cases first (plan §4.1 step 4): (is_clf, n_classes, codes)
    yield (True, 1, [])                       # empty target array
    yield (False, 1, [])
    yield (True, 2, [0, 1])                   # binary, both classes
    yield (True, 2, [0, 0, 0])                # all one class
    yield (True, 2, [1, 1, 1, 1])
    yield (True, 3, [0, 1, 2, 2, 1, 0])       # multiclass, repeats
    yield (True, 5, [4, 3, 2, 1, 0])          # full-range, reversed
    yield (True, 5, [0])                      # singleton
    yield (False, 3, [7, 7, 7])               # regressor: codes irrelevant, pass-through
    yield (False, 1, [0, 1, 2, 3])
    yield (True, 10, list(range(10)))         # every class once
    for _ in range(n):
        is_clf = rng.random() < 0.5
        n_classes = rng.randint(1, 12)
        k = rng.randint(0, 30)
        codes = [rng.randint(0, n_classes - 1) for _ in range(k)]
        yield (is_clf, n_classes, codes)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for is_clf, n_classes, codes in fuzz_cases(N_FUZZ, rng):
        count += 1
        # Distinct integer labels: the lookup preserves the label IDENTITY; using
        # int labels (rather than the issue's strings) lets the differential
        # compare values directly. mapping.md §4: classes_[k] is the k-th label.
        labels = list(range(100, 100 + n_classes))
        classes_ = np.array(labels)
        # y is the integer-code array (Y_DTYPE floats holding integer codes).
        y_arr = np.array(codes, dtype=float)

        shadow = shadow_prepare(is_clf, labels, codes)
        oracle = oracle_prepare(is_clf, classes_, y_arr)

        if shadow != oracle:
            disagreements.append((is_clf, n_classes, codes, shadow, oracle))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for is_clf, nc, codes, sh, orc in disagreements:
            print("  is_clf=%r n_classes=%d codes=%r shadow=%r oracle=%r"
                  % (is_clf, nc, codes, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of prepareScorerTargets agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements "
          "(classifier: classes_[y.astype(int)]; regressor: pass-through)."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
