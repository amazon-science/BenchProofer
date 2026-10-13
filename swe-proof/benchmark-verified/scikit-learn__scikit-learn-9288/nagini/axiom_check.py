#!/usr/bin/env python3
"""G-AX executable soundness check for scikit-learn__scikit-learn-9288.

Executes the REAL unchanged pseudo-random primitives that model.py abstracts
(`source_state`, `advance`, `draw`) and asserts that every observation matches
the model, including the discriminating fact the model's specification relies on.

model.py models the per-restart randomness as one up-front vector of independent
restart seeds drawn from one shared source whose internal state ADVANCES between
draws:

    seed_vector(s, n) = [draw(s), draw(advance(s)), draw(advance(advance(s))), ...]
                        (n terms)

where the source's initial state for an integer configuration is
`source_state(config)`. `source_state`, `advance`, and `draw` are abstract pure
functions; their real counterparts are:

  - `source_state(config)`  <->  the internal state of
        sklearn.utils.check_random_state(config) == numpy RandomState(config)
        (the unchanged configuration-to-source step k_means calls once).
  - `advance(state)` / `draw(state)`  <->  the per-draw state transition and the
        int a single draw yields when that one shared RandomState is drawn from
        via randint(np.iinfo(np.int32).max, size=n_init) (numpy RandomState).

The model's verification relies on the up-front draw vector being a genuine
ADVANCING sequence (its entries are position-dependent, NOT one shared source
value repeated across restarts): a constant per-restart seed (the one live
object handed to every restart) cannot satisfy
`Result() == seed_vector(...)`. G-AX validates that discriminating fact against
the real callees:

  (A-reference 1) the up-front vector randint(int32.max, size=n_init) has
      position-dependent entries (it advances; entries are not all identical)
      over many seeds -- so the abstract draw/advance really move the
      observable seed;
  (A-reference 2) handing the one live RandomState object to each restart (the
      pre-patch single-worker path) makes restart 0's effective seed differ
      from the up-front seeds[0] -- the bug path the model forbids;
  (end-to-end) the real, patched KMeans yields IDENTICAL labels_ for n_jobs=1
      and n_jobs=2 at the same random_state, exactly the behaviour the F2P test
      pins and the model encodes.

Imports only numpy (the real RNG the patch draws from) and the repository's own
sklearn (the very module the gold patch edits); nothing else. Exit 0 iff every
obligation holds.
"""
import sys

import numpy as np


def _upfront_seed_vector(config, n_init):
    """Reproduce the patch's up-front draw: one shared RandomState seeded by
    `config`, drawn once as randint(int32.max, size=n_init). Returns the vector
    of per-restart seeds (the observable `seed_vector`)."""
    from sklearn.utils import check_random_state
    rng = check_random_state(config)            # int branch -> RandomState(config)
    return [int(s) for s in rng.randint(np.iinfo(np.int32).max, size=n_init)]


def check_upfront_vector_advances():
    """(A-reference 1) The up-front draw vector has position-dependent entries
    (it ADVANCES) -- i.e. abstract draw/advance are a real move, so successive
    restart seeds are NOT all identical. (For n_init >= 2; int32.max collision
    probability is negligible.)"""
    for config in range(0, 50):
        vec = _upfront_seed_vector(config, 5)
        assert len(set(vec)) == len(vec), (
            "up-front draw vector should have distinct (advancing) entries for "
            "config %r, got %r -- draw/advance are not moving the seed" % (
                config, vec))
        # determinism: re-drawing from the same config gives the same vector
        assert _upfront_seed_vector(config, 5) == vec, (
            "up-front draw vector should be a deterministic function of the "
            "configuration for config %r" % (config,))


def check_live_object_reuse_diverges():
    """(A-reference 2) The fix runs restart i with a FRESH source seeded by the
    i-th up-front draw (a fresh RandomState(seeds[i])), whereas the pre-patch
    single-worker path hands the one live source (RandomState(config)) to every
    restart. These produce different per-restart randomness, so the bug path the
    model forbids genuinely diverges from the up-front draw vector the fix uses.

    We witness the divergence at restart 0 (the simplest, sentinel case): the
    randomness a fresh RandomState(seeds[0]) emits differs from the randomness
    the live RandomState(config) emits -- restart 0 under the fix and under the
    bug therefore explore different clusterings."""
    from sklearn.utils import check_random_state
    for config in range(0, 50):
        seeds = _upfront_seed_vector(config, 5)
        # fix: restart 0 is run from a fresh source seeded by the 0-th draw
        fresh0 = check_random_state(int(seeds[0]))   # RandomState(seeds[0])
        fresh_draw = int(fresh0.randint(np.iinfo(np.int32).max))
        # bug: the one live source handed to restart 0 (the n_jobs==1 path did
        # NOT pre-draw the seeds vector; the object is the initial
        # RandomState(config)).
        live = check_random_state(config)            # RandomState(config)
        live_draw = int(live.randint(np.iinfo(np.int32).max))
        assert fresh_draw != live_draw, (
            "fix's fresh source RandomState(seeds[0]) should produce different "
            "randomness than the bug's live RandomState(config) for config %r: "
            "fresh=%r live=%r" % (config, fresh_draw, live_draw))


def check_real_kmeans_njobs_consistent():
    """(end-to-end) The real, patched KMeans yields IDENTICAL labels_ for
    n_jobs=1 and n_jobs=2 at the same random_state -- the exact F2P observation
    the model pins via the shared up-front draw vector."""
    from sklearn.cluster import KMeans
    rnd = np.random.RandomState(0)
    X = rnd.normal(size=(50, 10))
    result_1 = KMeans(n_clusters=3, random_state=0, n_jobs=1).fit(X).labels_
    result_2 = KMeans(n_clusters=3, random_state=0, n_jobs=2).fit(X).labels_
    assert np.array_equal(result_1, result_2), (
        "patched KMeans should give identical labels_ for n_jobs=1 vs n_jobs=2 "
        "at the same random_state; got %r vs %r" % (
            list(result_1), list(result_2)))

    # a small sweep over seeds / cluster counts, to be safe
    for seed in range(0, 5):
        Xs = np.random.RandomState(seed).normal(size=(40, 4))
        for k in (2, 3):
            r1 = KMeans(n_clusters=k, random_state=seed, n_jobs=1).fit(Xs).labels_
            r2 = KMeans(n_clusters=k, random_state=seed, n_jobs=2).fit(Xs).labels_
            assert np.array_equal(r1, r2), (
                "patched KMeans n_jobs mismatch at seed=%r k=%r" % (seed, k))


def main():
    check_upfront_vector_advances()
    check_live_object_reuse_diverges()
    check_real_kmeans_njobs_consistent()
    print("G-AX OK: up-front draw vector advances (A-reference 1) over 50 "
          "configs; fresh-per-restart source diverges from the live shared "
          "source (A-reference 2) over 50 configs; real patched KMeans labels_ "
          "are n_jobs-invariant (end-to-end).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
