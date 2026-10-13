#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-13124.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo types (per-class counts -> a shared
              random source threaded across classes -> per-class permutations),
              wrapped in the UNCHANGED surrounding structure (KFold contiguous
              fold assignment + scatter into `test_folds`). The A-tagged callee
              `shuffleAfter` is NOT replaced by an axiom model here; G-CONF
              isolates the R/I legs, so the A callee is left as the *real* repo
              callee: one `numpy.random.RandomState(seed)` consumed in sequence,
              exactly what the patched code threads through the per-class KFold.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `StratifiedKFold._make_test_folds` applied at base_commit (the real
              correctness oracle, G-RESOLVE). The harness applies patch.diff
              before this runs, so the import is the patched version.

They must agree on every Requires-satisfying input (valid binary/multiclass `y`,
`n_splits` >= 2 and <= the smallest class count). Exit 0 iff zero disagreements;
any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image). The fuzz seed is
pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

import numpy as np

SEED = 13124
N_FUZZ = 100_000


def shadow_make_test_folds(y, n_splits, rs_seed):
    """The R/I shadow of Solution.lean's impl region (`perClassShuffles`,
    `threadAll`/`threadStep`/`blockSize`) wrapped in the unchanged surrounding
    I-structure. `shuffleAfter` (the A callee) is the REAL numpy shuffle of a
    SINGLE shared RandomState, consumed sequentially across classes."""
    y = np.asarray(y)
    n_samples = y.shape[0]
    unique_y, y_inversed = np.unique(y, return_inverse=True)
    y_counts = np.bincount(y_inversed)

    # impl region (R/I): thread ONE shared source across the classes in order.
    # `shuffleAfter s prev sz` == "shuffle a block of size sz from the source
    # already advanced by shuffling blocks of sizes prev" -> exactly the real
    # numpy RandomState consumed in sequence (block size = max(count, n_splits)).
    rng = np.random.RandomState(rs_seed)
    per_cls_perms = []
    for count in y_counts:
        idx = np.arange(max(count, n_splits))   # KFold.split(np.zeros(max(c, n_splits)))
        rng.shuffle(idx)                          # shared source advances (threading)
        per_cls_perms.append(idx)

    # unchanged surrounding I-structure: KFold contiguous fold assignment, then
    # scatter each class's test indices into test_folds (identical pre/post-patch).
    def kfold_test_splits(n, perm):
        fold_sizes = np.full(n_splits, n // n_splits, dtype=int)
        fold_sizes[: n % n_splits] += 1
        out, cur = [], 0
        for fs in fold_sizes:
            out.append(perm[cur:cur + fs])
            cur += fs
        return out

    per_cls_cvs = [
        kfold_test_splits(max(c, n_splits), per_cls_perms[ci])
        for ci, c in enumerate(y_counts)
    ]
    test_folds = np.zeros(n_samples, dtype=int)
    for tfi, per_cls_splits in enumerate(zip(*per_cls_cvs)):
        for cls, test_split in zip(unique_y, per_cls_splits):
            cls_test_folds = test_folds[y == cls]
            test_split = test_split[test_split < len(cls_test_folds)]
            cls_test_folds[test_split] = tfi
            test_folds[y == cls] = cls_test_folds
    return list(int(v) for v in test_folds)


def oracle_make_test_folds(y, n_splits, rs_seed):
    """patch.diff's behaviour: the patched StratifiedKFold._make_test_folds
    (rng = check_random_state(self.random_state)). The harness applies patch.diff
    before this runs, so the import is the patched version."""
    from sklearn.model_selection import StratifiedKFold
    y = np.asarray(y)
    X = np.zeros((y.shape[0], 1))
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=rs_seed)
    return list(int(v) for v in skf._make_test_folds(X, y))


def fuzz_inputs(n, rng):
    # boundary cases first
    yield ([0] * 5 + [1] * 5, 5, 0)        # the F2P scenario, seed 0
    yield ([0] * 5 + [1] * 5, 5, 1)        # the F2P scenario, seed 1
    yield ([0, 0, 1, 1], 2, 0)
    yield ([0, 1] * 3, 2, 42)
    yield ([0] * 2 + [1] * 2 + [2] * 2, 2, 7)
    for _ in range(n):
        n_splits = rng.randint(2, 5)
        n_classes = rng.randint(2, 4)
        counts = [rng.randint(n_splits, n_splits + 6) for _ in range(n_classes)]
        y = []
        for c in range(n_classes):
            y += [c] * counts[c]
        rng.shuffle(y)
        rs_seed = rng.randint(0, 10_000)
        yield (y, n_splits, rs_seed)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for (y, n_splits, rs_seed) in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_make_test_folds(y, n_splits, rs_seed)
        oracle = oracle_make_test_folds(y, n_splits, rs_seed)
        if shadow != oracle:
            disagreements.append((y, n_splits, rs_seed, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for y, ns, rs, sh, orc in disagreements:
            print("  y=%r n_splits=%d seed=%d shadow=%r oracle=%r"
                  % (y, ns, rs, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of perClassShuffles (threaded shared source + "
          "unchanged fold structure) agrees with patch.diff behaviour on %d "
          "inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
