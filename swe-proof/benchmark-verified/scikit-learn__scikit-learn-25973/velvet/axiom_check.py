#!/usr/bin/env python3
"""G-AX executable soundness check for scikit-learn__scikit-learn-25973.

Validates the ONE kind-A construct of the bundle — the A-reference deep model
`materialize` (Solution.lean `pure` region) against the REAL repo callee it
models, `sklearn.model_selection.check_cv`.

`materialize` claims: buffering a possibly single-pass split source yields a
re-readable source carrying the SAME split sequence — i.e.

    (materialize s).reusable = true            -- re-readable
    (materialize s).splits   = s.splits         -- same splits, none dropped/added
    readObs (materialize s)  = (materialize s).splits  on every read

The real `check_cv`, for a raw iterable / generator `cv`, returns
`_CVIterableWrapper(cv)` whose `__init__` does `self.cv = list(cv)` (materializes
the generator ONCE) and whose `.split(...)` re-iterates that stored list every
call. So `check_cv` is the executable witness of `materialize`'s claim.

The checks (over boundary + fuzzed split sequences, each fed as a fresh one-shot
GENERATOR — the exhaustion-prone case the bug hit):

  (1) re-readability      reading the materialized source TWICE yields the
                          identical full split sequence both times
                          (== `materialize`'s `reusable = true`).
  (2) same-splits         the materialized source's split sequence equals the
                          ORIGINAL generator's full sequence — no split dropped,
                          added, or reordered (== `(materialize s).splits =
                          s.splits`).
  (3) discriminator real  the UN-buffered baseline (reading the raw generator
                          twice, as pre-patch did) loses the splits on the second
                          read — establishing the bug the materialize step fixes
                          is genuine, so the A-reference is load-bearing not dead.

Imports only `numpy` + `sklearn.model_selection` (the module the gold patch
imports `check_cv` from). The RNG seed is pinned (mapping.md section 4) for a
reproducible verdict. Exit 0 iff every obligation holds.
"""
import sys

import numpy as np
from sklearn.model_selection import check_cv

SEED = 25973


def make_split_sequence(rng, n_splits, n_samples):
    """A list of (train_idx, test_idx) splits — the abstract `splits` sequence a
    CvSource represents (mapping.md section 2). Returned as a plain list so we
    can both (a) build a fresh generator from it and (b) compare against it."""
    splits = []
    for _ in range(n_splits):
        perm = rng.permutation(n_samples)
        cut = max(1, n_samples // 2)
        test = np.sort(perm[:cut])
        train = np.sort(perm[cut:])
        splits.append((train, test))
    return splits


def one_shot_generator(splits):
    """A single-pass generator of (train, test) splits — exactly the shape the
    bug report passes (`LeaveOneGroupOut().split(...)`). Consumed after one
    full iteration."""
    for tr, te in splits:
        yield tr, te


def fingerprint(splits):
    """Order-sensitive, content-sensitive fingerprint of a split sequence so we
    can compare two reads for exact equality (numpy arrays need tolist)."""
    return [(tr.tolist(), te.tolist()) for tr, te in splits]


def read_via_real_check_cv(gen):
    """materialize: real `check_cv` on a raw iterable -> a re-readable cv object.
    Returns the cv object; classifier flag is irrelevant on the iterable path
    (mapping.md section 3.1)."""
    return check_cv(gen, y=None, classifier=False)


def read_splits(cv_obj):
    """One read (`readObs`) of a materialized cv object: iterate cv.split()."""
    return list(cv_obj.split(X=None, y=None, groups=None))


def main():
    rng = np.random.RandomState(SEED)

    # boundary + fuzzed split-sequence shapes (n_splits, n_samples)
    cases = [(1, 4), (2, 6), (3, 10), (5, 20), (1, 2), (4, 8)]
    for _ in range(2000):
        cases.append((int(rng.randint(1, 8)), int(rng.randint(2, 30))))

    checked = 0
    for n_splits, n_samples in cases:
        base = make_split_sequence(rng, n_splits, n_samples)
        expected = fingerprint(base)

        # --- (1) re-readability + (2) same-splits, via REAL check_cv ---------
        gen = one_shot_generator(base)            # fresh one-shot generator
        cv_obj = read_via_real_check_cv(gen)      # materialize (real callee)
        first = fingerprint(read_splits(cv_obj))  # read #1
        second = fingerprint(read_splits(cv_obj)) # read #2 (must NOT be empty)
        assert first == expected, (
            "materialize A-reference unsound (same-splits): check_cv-buffered "
            "first read %r != original generator sequence %r" % (first, expected))
        assert second == expected, (
            "materialize A-reference unsound (re-readability): check_cv-buffered "
            "second read %r != first read %r (source not re-readable)"
            % (second, expected))

        # --- (3) discriminator is real: un-buffered raw generator is one-shot -
        raw = one_shot_generator(base)
        raw_first = fingerprint(list(raw))        # read #1 consumes it
        raw_second = fingerprint(list(raw))       # read #2 sees nothing
        assert raw_first == expected, (
            "sanity: raw generator first read %r != %r" % (raw_first, expected))
        assert raw_second == [], (
            "discriminator not real: raw generator second read %r should be "
            "empty (one-shot exhaustion is the bug) " % (raw_second,))

        checked += 1

    print("G-AX OK: materialize deep model (== real check_cv) sound on %d "
          "split-sequence cases (seed=%d): check_cv-buffered source is "
          "re-readable with identical splits on both reads; un-buffered raw "
          "generator is exhausted after one read (the discriminator is real)."
          % (checked, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
