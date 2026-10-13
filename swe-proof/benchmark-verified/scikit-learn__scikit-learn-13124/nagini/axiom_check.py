#!/usr/bin/env python3
"""G-AX executable soundness check for scikit-learn__scikit-learn-13124.

Executes the REAL unchanged pseudo-random primitives that model.py abstracts
(`seed_state`, `advance`) and asserts that every observation matches the model,
including the discriminating fact the model's specification relies on.

model.py models the per-class randomized draw as one shared pseudo-random
source whose internal state ADVANCES between classes:

    state_stream(s, n) = [s, advance(s), advance(advance(s)), ...]   (n terms)

where the source's initial state for an integer seed is `seed_state(seed)`.
`seed_state` and `advance` are abstract pure functions; their real
counterparts are:

  - `seed_state(seed)`  <->  the internal state of
        sklearn.utils.check_random_state(seed) == numpy RandomState(seed)
        (the unchanged seed-to-source conversion the fix calls).
  - `advance(state)`    <->  the state transition performed when that one
        shared RandomState is drawn from once per class
        (numpy RandomState.shuffle of a per-class index vector).

The model's verification relies on `advance` being a genuine state MOVE: a
constant per-class draw (every class re-seeded from the same state) cannot
satisfy `Result() == state_stream(...)`. G-AX validates that discriminating
fact against the real callees:

  (A-reference 1) one shared generator drawn once per class yields per-class
      permutations that ADVANCE (successive classes differ) -- so `advance`
      really moves the observable draw;
  (A-reference 2) re-seeding a fresh generator from the same integer seed for
      every class yields IDENTICAL per-class permutations -- the pre-patch
      behaviour the model forbids;
  (end-to-end) the real, patched StratifiedKFold._make_test_folds makes the
      sorted per-fold test sets DEPEND on the seed (two seeds -> different
      sets), exactly the behaviour the F2P test pins and the model encodes.

Imports only numpy (the real RNG the patch's check_random_state wraps) and the
repository's own sklearn (the very module the gold patch edits); nothing else.
Exit 0 iff every obligation holds.
"""
import sys

import numpy as np


def _kfold_test_perm(n_samples, n_splits, rng_like):
    """Reproduce KFold(shuffle=True, random_state=rng_like)._iter_test_indices
    ordering for a single class: shuffle indices with the source obtained from
    `rng_like`, then read them back in fold order. Returns the permutation as a
    tuple (the observable per-class draw)."""
    from sklearn.utils import check_random_state
    indices = np.arange(n_samples)
    check_random_state(rng_like).shuffle(indices)
    return tuple(int(x) for x in indices)


def check_shared_generator_advances():
    """(A-reference 1) A single shared RandomState drawn once per class gives
    per-class permutations that ADVANCE -- i.e. the abstract `advance` is a
    real state move, so successive class draws are NOT all identical."""
    for seed in range(0, 25):
        rng = np.random.RandomState(seed)        # check_random_state(int)
        # draw one permutation per class from the SAME advancing source
        draws = [_kfold_test_perm(5, 5, rng) for _ in range(2)]
        assert draws[0] != draws[1], (
            "shared advancing source produced identical per-class draws for "
            "seed %r: %r -- `advance` is not moving the state" % (seed, draws))


def check_reseed_is_constant():
    """(A-reference 2) Re-seeding a FRESH RandomState from the same integer
    seed for every class (the pre-patch path the model forbids) gives IDENTICAL
    per-class permutations -- confirming the model's discriminator is exactly
    the difference between the two paths."""
    for seed in range(0, 25):
        # pre-patch: rng = self.random_state (raw int); each class re-converts
        draws = [_kfold_test_perm(5, 5, seed) for _ in range(3)]
        assert draws[0] == draws[1] == draws[2], (
            "re-seeding from the same int should give identical per-class "
            "draws for seed %r, got %r" % (seed, draws))


def check_real_stratifiedkfold_seed_dependent():
    """(end-to-end) The real, patched StratifiedKFold makes the sorted per-fold
    test sets depend on the seed -- the exact F2P observation the model pins
    via the advancing stream."""
    from sklearn.model_selection import StratifiedKFold
    X = np.arange(10)
    y = [0] * 5 + [1] * 5

    def sorted_test_sets(seed):
        kf = StratifiedKFold(5, shuffle=True, random_state=seed)
        return sorted(tuple(int(i) for i in s[1]) for s in kf.split(X, y))

    s0 = sorted_test_sets(0)
    s1 = sorted_test_sets(1)
    assert s0 != s1, (
        "patched StratifiedKFold should give seed-dependent sorted test sets; "
        "got identical sets for seeds 0 and 1: %r" % (s0,))

    # larger, multi-seed sweep: distinct seeds should not collapse to one set
    seen = {}
    X2 = np.arange(40)
    y2 = [0] * 20 + [1] * 20
    for seed in range(0, 12):
        kf = StratifiedKFold(5, shuffle=True, random_state=seed)
        key = tuple(sorted(tuple(int(i) for i in s[1])
                           for s in kf.split(X2, y2)))
        seen.setdefault(key, []).append(seed)
    assert len(seen) > 1, (
        "patched StratifiedKFold collapsed all seeds to a single sorted "
        "test-set assignment: %r" % (list(seen.values()),))


def main():
    check_shared_generator_advances()
    check_reseed_is_constant()
    check_real_stratifiedkfold_seed_dependent()
    print("G-AX OK: shared source advances (A-reference) over 25 seeds; "
          "re-seed is constant over 25 seeds; real patched StratifiedKFold "
          "test sets are seed-dependent (end-to-end).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
