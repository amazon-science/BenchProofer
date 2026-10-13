#!/usr/bin/env python
"""G-CONF: differential conformance for scikit-learn__scikit-learn-13124.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). The bundle models ONE behavior: how
`StratifiedKFold._make_test_folds` THREADS its single random generator across the
per-class fold splitters (`implementation_classOrders`, mapping.md /
refinement.md). The soundness-critical decision the patch changes is one line —
`rng = self.random_state` becomes `rng = check_random_state(self.random_state)`.
That turns `rng` from a raw int seed (re-seeded fresh for every class, so the
generator never advances) into a single `RandomState` instance that ADVANCES as
each class consumes it. We isolate exactly the per-class shuffle ORDERS this
produces.

ORACLE = the genuine post-patch path, reconstructed from the REAL unchanged
repo callees: `sklearn.utils.check_random_state` builds the one generator from
the seed, and the per-class shuffle is `np.arange(max(count, n_splits))` shuffled
in place by `RandomState.shuffle` — exactly `KFold(shuffle=True,
random_state=rng)._iter_test_indices`'s shuffle (sklearn/.../_split.py L423-427),
with the SAME generator threaded in class order (the L653-658 comprehension
consumed by zip).

SHADOW_FIX = the op-for-op transliteration of `implementation_classOrders`
(Solution.lean impl region): seed ONE generator, consume it once per class
carrying the advanced state forward. Must EQUAL the oracle on every input.

SHADOW_BUG = the transliteration of `Solution_prepatch.lean` (re-seed from the
SAME seed every class). Negative control: the differential test must be powerful
enough to tell the bug apart from the fix on at least one configuration.

Exit 0 iff (a) zero fix-vs-oracle disagreements AND (b) the bug shadow disagrees
on >= 1 configuration, over a discrete edge matrix + >=1e5 fuzzed draws.
stdlib-driven fuzzing (pinned seed 13124); numpy generators are seeded by the
per-draw seed, matching the real code path.
"""
import random
import sys

import numpy as np

try:
    from sklearn.utils import check_random_state  # REAL unchanged callee
except Exception as e:  # pragma: no cover
    print("status=error could not import sklearn.utils.check_random_state:", e)
    sys.exit(2)

SEED = 13124
N_RANDOM = 120_000  # >= 1e5


# ---- ORACLE: genuine post-patch threading via the REAL repo callees ---------
# rng = check_random_state(seed)  (one generator)
# per class: indices = np.arange(max(count, n_splits)); rng.shuffle(indices)
# (this is KFold._iter_test_indices' shuffle; the SAME rng is threaded.)
def oracle_orders(seed, shuffle, n_splits, counts):
    if not shuffle:
        return [list(range(max(c, n_splits))) for c in counts]
    rng = check_random_state(seed)            # REAL callee (int -> RandomState)
    orders = []
    for c in counts:
        idx = np.arange(max(c, n_splits))
        rng.shuffle(idx)                      # REAL callee, ADVANCES rng
        orders.append([int(x) for x in idx])
    return orders


# ---- SHADOW_FIX: transliteration of implementation_classOrders --------------
# Threads ONE generator; carries the advanced state forward (st := res.2).
def _shuffleN(rng, m):
    idx = np.arange(m)
    rng.shuffle(idx)
    return [int(x) for x in idx]


def shadow_fix(seed, shuffle, n_splits, counts):
    if not shuffle:
        return [list(range(max(c, n_splits))) for c in counts]
    st = check_random_state(seed)             # seedState seed
    orders = []
    for c in counts:
        orders.append(_shuffleN(st, max(c, n_splits)))   # shuffleN st (max c nFolds)
    return orders                                        # st carried forward implicitly


# ---- SHADOW_BUG: transliteration of Solution_prepatch.lean ------------------
# Re-derives a FRESH generator from the same seed every class (no threading).
def shadow_bug(seed, shuffle, n_splits, counts):
    if not shuffle:
        return [list(range(max(c, n_splits))) for c in counts]
    orders = []
    for c in counts:
        st = check_random_state(seed)         # shuffleN (seedState seed) ...  every iter
        orders.append(_shuffleN(st, max(c, n_splits)))
    return orders


def edge_matrix():
    cases = []
    # shuffle off: order is natural ascending regardless of seed.
    cases.append((0, False, 2, [5, 5]))
    cases.append((7, False, 5, [10, 10]))
    # shuffle on: >=2 equal-length classes (the issue's reproducer shape).
    cases.append((0, True, 5, [5, 5]))
    cases.append((1, True, 5, [5, 5]))
    cases.append((0, True, 10, [10, 10]))     # exactly the problem_statement case
    cases.append((2, True, 2, [3, 4, 5]))
    cases.append((0, True, 3, [3]))           # single class
    cases.append((0, True, 2, []))            # no classes
    cases.append((42, True, 2, [2, 2, 2, 2]))
    return cases


def main():
    fix_disagree = 0
    bug_disagree = 0
    checked = 0

    def check(seed, shuffle, n_splits, counts):
        nonlocal fix_disagree, bug_disagree, checked
        checked += 1
        o = oracle_orders(seed, shuffle, n_splits, counts)
        f = shadow_fix(seed, shuffle, n_splits, counts)
        if f != o:
            fix_disagree += 1
            if fix_disagree <= 5:
                print("FIX!=ORACLE seed=%r shuffle=%r n_splits=%r counts=%r\n"
                      "  oracle=%r\n  fix   =%r" % (seed, shuffle, n_splits, counts, o, f))
        b = shadow_bug(seed, shuffle, n_splits, counts)
        if b != o:
            bug_disagree += 1

    for c in edge_matrix():
        check(*c)

    rnd = random.Random(SEED)
    for _ in range(N_RANDOM):
        n_splits = rnd.randint(2, 6)
        shuffle = rnd.random() < 0.7
        n_classes = rnd.randint(0, 5)
        # counts >= n_splits is the in-domain regime; also probe a few smaller.
        counts = [rnd.randint(max(1, n_splits - 1), n_splits + 8)
                  for _ in range(n_classes)]
        seed = rnd.randint(0, 10_000)
        check(seed, shuffle, n_splits, counts)

    print("checked=%d fix_disagreements=%d bug_disagreements=%d"
          % (checked, fix_disagree, bug_disagree))
    if fix_disagree != 0:
        print("status=fail impl shadow disagrees with genuine post-patch threading")
        sys.exit(1)
    if bug_disagree == 0:
        print("status=fail differential test has NO power: prepatch (re-seed) "
              "never distinguished from the fix (threading)")
        sys.exit(1)
    print("status=ok impl shadow == genuine post-patch threading on all %d "
          "configs; prepatch distinguished on %d" % (checked, bug_disagree))
    sys.exit(0)


if __name__ == "__main__":
    main()
