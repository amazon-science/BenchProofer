#!/usr/bin/env python3
"""G-AX executable soundness check for scikit-learn__scikit-learn-13124.

Validates the single A-reference of this bundle: the opaque axiom

    shuffleAfter : Int -> List Nat -> Nat -> List Nat

is a sound, deterministic model of the REAL community callee it stands for — a
standard pseudo-random generator (numpy's `RandomState`) whose source is
consumed in sequence. `shuffleAfter s prev sz` is defined to be "the permutation
the source selected by `s` yields for a block of size `sz`, AFTER that same
source has already been consumed to permute blocks of sizes `prev` in order"
(the residue model of mapping.md §3.1).

What G-AX confirms against the real callee (`numpy.random.RandomState`, the same
generator the patched code threads through the per-class `KFold`):

  (1) WELL-DEFINEDNESS / DETERMINISM. `shuffleAfter` is a genuine function of
      exactly its three arguments: re-running the real source on the same
      `(s, prev, sz)` yields the same permutation every time. A Lean axiom of
      type `Int -> List Nat -> Nat -> List Nat` requires this.

  (2) THREADING IS REAL (the residue is load-bearing). The result depends on the
      WHOLE residue `prev`, not just `sz`: a block permuted after earlier blocks
      generally differs from the same block permuted from the fresh source
      (`prev = []`). This is exactly the property the patch restores and the bug
      destroyed (the buggy code restarts the source per class -> residue ignored
      -> every class gets `shuffleAfter s [] sz`). The check asserts that the
      threaded result differs from the reset result on a non-trivial fraction of
      configurations, so the model is not vacuously equal to the buggy one.

  (3) SEED SENSITIVITY (grounds the F2P assertion). Two distinct configuration
      values `s` generally give distinct permutations for the same `(prev, sz)`,
      so distinct seeds yield distinct per-class shuffles.

Imports only numpy (the real generator) + stdlib. Exit 0 iff every obligation
holds.
"""
import random
import sys

import numpy as np


def real_shuffle_after(s, prev, sz):
    """The REAL callee: one RandomState(s) consumed in sequence — shuffle a block
    of each size in `prev` (advancing the source, discarding the results), then
    shuffle and return the block of size `sz`. This is precisely what the patched
    per-class loop does (`rng = check_random_state(seed)` threaded across the
    per-class `KFold(..., random_state=rng).split(np.zeros(max(count, n_splits)))`
    calls)."""
    rng = np.random.RandomState(s)
    for p in prev:
        idx = np.arange(p)
        rng.shuffle(idx)            # advance the shared source
    block = np.arange(sz)
    rng.shuffle(block)
    return [int(v) for v in block]


def main():
    rng = random.Random(13124)

    # --- (1) determinism: shuffleAfter is a function of (s, prev, sz) ---------
    det_cases = 0
    for _ in range(3000):
        s = rng.randint(0, 10_000)
        k = rng.randint(0, 4)
        prev = [rng.randint(2, 12) for _ in range(k)]
        sz = rng.randint(2, 12)
        a = real_shuffle_after(s, prev, sz)
        b = real_shuffle_after(s, prev, sz)
        assert a == b, ("shuffleAfter non-deterministic on (s=%r, prev=%r, "
                        "sz=%r): %r vs %r" % (s, prev, sz, a, b))
        # a permutation of range(sz)
        assert sorted(a) == list(range(sz)), (
            "shuffleAfter(%r,%r,%r)=%r is not a permutation of range(%d)"
            % (s, prev, sz, a, sz))
        det_cases += 1

    # --- (2) threading is real: the residue prev changes the result ----------
    threaded_differs = 0
    threaded_total = 0
    for _ in range(3000):
        s = rng.randint(0, 10_000)
        k = rng.randint(1, 4)
        prev = [rng.randint(3, 12) for _ in range(k)]
        sz = rng.randint(3, 12)
        threaded = real_shuffle_after(s, prev, sz)
        reset = real_shuffle_after(s, [], sz)   # the buggy reset (residue ignored)
        threaded_total += 1
        if threaded != reset:
            threaded_differs += 1
    # On a healthy generator, a non-empty residue changes the block permutation
    # for the large majority of configurations. Require a substantial fraction so
    # a regression to the buggy (reset) behaviour cannot pass this gate.
    assert threaded_differs >= 0.5 * threaded_total, (
        "threading appears inert: residue changed the permutation in only "
        "%d/%d cases" % (threaded_differs, threaded_total))

    # --- (3) seed sensitivity: distinct s -> distinct permutations -----------
    seed_differs = 0
    seed_total = 0
    for _ in range(3000):
        s1 = rng.randint(0, 10_000)
        s2 = rng.randint(0, 10_000)
        if s1 == s2:
            continue
        k = rng.randint(0, 3)
        prev = [rng.randint(3, 12) for _ in range(k)]
        sz = rng.randint(3, 12)
        seed_total += 1
        if real_shuffle_after(s1, prev, sz) != real_shuffle_after(s2, prev, sz):
            seed_differs += 1
    assert seed_differs >= 0.5 * seed_total, (
        "seed appears inert: distinct seeds gave distinct permutations in only "
        "%d/%d cases" % (seed_differs, seed_total))

    print("G-AX OK: shuffleAfter A-reference sound vs real numpy RandomState - "
          "deterministic on %d cases; residue load-bearing (%d/%d threaded != "
          "reset); seed sensitive (%d/%d distinct)." % (
              det_cases, threaded_differs, threaded_total, seed_differs,
              seed_total))
    return 0


if __name__ == "__main__":
    sys.exit(main())
