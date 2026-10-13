#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-9288
(nagini).

SHADOW: the impl region of model.py `restart_seeds`, copied verbatim below
with the contract calls (Requires/Ensures/Invariant/Assert) stripped. The
@Pure helper `seed_vector` copies over as a plain function on an immutable
PSeq tuple shim. The three @Pure @ContractOnly abstract callees
(`source_state` / `advance` / `draw`) are realized by the REAL counterparts
mapping.md binds them to:

  - source_state(config): the internal state of
    sklearn.utils.check_random_state(config) on the integer branch (one
    numpy RandomState built from the integer configuration), carried as the
    opaque value get_state() returns;
  - draw(state): the int a single randint(np.iinfo(np.int32).max) draw
    yields at that state;
  - advance(state): the state after one such draw.

ORACLE: the REAL patched repo function the model models per mapping.md — the
per-restart seed handling of `sklearn.cluster.k_means_.k_means` on its
single-worker path. Observed by instrumenting the per-restart worker
(`_kmeans_single_lloyd` / `_kmeans_single_elkan`) to record the random_state
value each restart receives, then running the real k_means with n_jobs=1 on a
fixed small data matrix. The matrix, sample weights, init, tolerance,
algorithm selection and the kept-result selection are unchanged machinery
orthogonal to the modeled seed data-flow (mapping.md section 2), so a fixed
instantiation of them observes exactly the modeled quantity: the seed vector
the single-worker strategy consumes. The gate applies patch.diff to /testbed
before this script runs; PYTHONPATH=/testbed makes the patched module
importable — this script does NOT apply any patch itself.

Type bridge (mapping.md section 2): the integer configuration maps
identically to `config`; the restart count maps identically to `n_restarts`;
a pseudo-random source is modeled by its internal state (opaque here,
threaded via get_state/set_state — the model's int carrier is an abstraction
of the same state value and the impl only passes it around, never computes
on it); the per-restart seed list is List[int], compared elementwise as
Python ints.

Input domain: Requires demands n_restarts >= 0. The real callee rejects a
non-positive restart count with a ValueError instead of returning a value,
so oracle-diffed generation is restricted to n_restarts >= 1 — the callee's
operating domain (the n_restarts == 0 boundary is exercised shadow-side
against the pure fold, which is empty there). The integer configuration
ranges over the values the source constructor accepts: 0 <= config < 2**32.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz pairs.
Pinned fuzz seed: 92880.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + numpy only.
"""
import json
import random
import sys
import warnings

import numpy as np

SEED = 92880
N_FUZZ = 100_000


# --- PSeq shim: immutable sequence, the operations the pure region uses ------

class PSeq:
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __hash__(self):
        return hash(self._t)


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- the abstract @ContractOnly callees, realized by the REAL counterparts ---

_INT32_MAX = None  # np.iinfo(np.int32).max, set in main after import checks


def source_state(config):
    from sklearn.utils import check_random_state
    rng = check_random_state(config)  # int branch -> one RandomState(config)
    return rng.get_state()


def draw(state):
    rng = np.random.RandomState()
    rng.set_state(state)
    return int(rng.randint(_INT32_MAX))


def advance(state):
    rng = np.random.RandomState()
    rng.set_state(state)
    rng.randint(_INT32_MAX)
    return rng.get_state()


# --- pure helper from model.py, contracts stripped ----------------------------

def seed_vector(s, n):
    if n == 0:
        return PSeq(0).take(0)
    return PSeq(draw(s)) + seed_vector(advance(s), n - 1)


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def restart_seeds(config, n_restarts):
    start = source_state(config)
    cur = start
    result = []  # type: list
    i = 0
    while i < n_restarts:
        result = result + [draw(cur)]
        cur = advance(cur)
        i = i + 1
    return result


# --- oracle: the real patched k_means, instrumented at the restart boundary ---

_captured = []


def _install_capture_stub():
    """Replace the per-restart worker with a stub that records the
    random_state value each restart receives and returns well-formed dummy
    results (the worker body is unchanged machinery, orthogonal to the
    modeled seed data-flow)."""
    import sklearn.cluster.k_means_ as km

    def stub(X, sample_weight, n_clusters, *args, **kwargs):
        rs = kwargs.get("random_state")
        try:
            _captured.append(int(rs))
        except (TypeError, ValueError):
            _captured.append("<non-integer random_state: %r>" % (type(rs),))
        n = X.shape[0]
        labels = (np.arange(n) % n_clusters).astype(np.int32)
        inertia = float(len(_captured))
        centers = np.zeros((n_clusters, X.shape[1]), dtype=X.dtype)
        return labels, inertia, centers, 1

    km._kmeans_single_lloyd = stub
    km._kmeans_single_elkan = stub
    return km


_ORACLE_X = np.array([[0.0, 0.0], [1.0, 0.0], [2.0, 1.0], [3.0, 3.0],
                      [4.0, 5.0]])


def oracle_seeds(km, config, n_restarts):
    """The per-restart random_state values the real single-worker path hands
    to its restarts for this configuration and restart count."""
    del _captured[:]
    km.k_means(_ORACLE_X, 2, n_init=n_restarts, random_state=config,
               n_jobs=1, algorithm="full")
    return list(_captured)


# --- differential driver -------------------------------------------------------

def check_pair(km, config, n_restarts):
    shadow = restart_seeds(config, n_restarts)
    real = oracle_seeds(km, config, n_restarts)
    if shadow != real:
        return ("DISAGREEMENT\n  config=%r n_restarts=%r\n  shadow=%r\n"
                "  real=%r" % (config, n_restarts, shadow, real))
    return None


def boundary_pairs():
    configs = [0, 1, 2, 42, 2**16, 2**31 - 1, 2**31, 2**32 - 1]
    ns = [1, 2, 3, 10]
    return [(c, n) for c in configs for n in ns] + [(0, 25), (2**32 - 1, 25)]


def main():
    global _INT32_MAX
    _INT32_MAX = int(np.iinfo(np.int32).max)
    warnings.simplefilter("ignore")

    km = _install_capture_stub()

    # shadow-side n == 0 boundary: the impl yields the empty list, matching
    # the pure fold (the real callee rejects a zero count, so no oracle call).
    assert restart_seeds(0, 0) == [] and len(seed_vector(source_state(0), 0)) == 0

    checked = 0
    for config, n in boundary_pairs():
        err = check_pair(km, config, n)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        config = rng.randrange(0, 2**32)
        # mostly small restart counts (the realistic regime around the
        # default), occasionally larger
        n = rng.randint(1, 8) if rng.random() < 0.95 else rng.randint(9, 20)
        err = check_pair(km, config, n)
        if err:
            print(err)
            return 1
        checked += 1

    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    print("G-CONF OK: shadow impl == real single-worker per-restart seeds on "
          "%d inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, len(boundary_pairs()), N_FUZZ, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
