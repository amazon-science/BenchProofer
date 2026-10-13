#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for scikit-learn__scikit-learn-12682.

The bundle models the argument bundle a sparse-coding estimator hands to the
underlying sparse-solver when it encodes data, as a pure function of the
construction-time options (mapping.md):

    n_components, transform_algorithm, transform_n_nonzero_coefs, transform_alpha,
    split_sign, n_jobs, positive_code, transform_max_iter

Post-patch rule: the estimator records every option, and when it encodes data it
assembles the solver-argument bundle from that stored configuration — in
particular the solver's iteration budget `max_iter` is the configured
`transform_max_iter` (not a fixed default of 1000).

This check runs against the REAL patched code (the orchestrator applies the gold
patch before running, `apply_gold=True`). For each fuzzed option tuple we build a
`SparseCoder(..., transform_max_iter=m)`, intercept the `sparse_encode(...)` call
that `transform()` makes (by monkeypatching the module-level `sparse_encode` to
capture its keyword arguments — the ORACLE), and compare the captured arguments
to the op-for-op transliteration of `implementation_codingSolverArgs` (the
SHADOW, refinement.md): each solver argument is the corresponding configured
option. They must agree on every input — in particular `max_iter` must equal the
configured `transform_max_iter` (the case the prepatch drops).

stdlib + numpy + sklearn (already in the instance image). Pinned seed: 12682.
"""
import random
import sys

SEED = 12682
N = 120_000

import importlib

import numpy as np
# NOTE: `import sklearn.decomposition.dict_learning as dl` binds the RE-EXPORTED
# function `dict_learning` (the package __init__ shadows the submodule of the
# same name), NOT the module — so `dl.sparse_encode` would be invalid. Fetch the
# real module object explicitly. `transform()` looks up `sparse_encode` as a
# module global of this module, so patching `dl.sparse_encode` here is the
# correct interception point.
dl = importlib.import_module("sklearn.decomposition.dict_learning")
from sklearn.decomposition import SparseCoder

# algorithm enum codes (mapping.md). transform()'s sparse_encode call forwards
# transform_algorithm verbatim; we fuzz the full set the estimator accepts.
ALGOS = ["omp", "lasso_lars", "lasso_cd", "lars", "threshold"]
ALGO_CODE = {a: i for i, a in enumerate(ALGOS)}


# --- ORACLE: arguments the REAL patched estimator hands to the solver --------
def oracle_args(algorithm, n_nonzero_coefs, alpha, n_jobs, positive, max_iter):
    """Construct the estimator and capture the kwargs of the sparse_encode call
    its transform() makes."""
    captured = {}
    real_sparse_encode = dl.sparse_encode

    def spy(X, dictionary, **kwargs):
        captured.update(kwargs)
        # return a correctly-shaped code so transform() can finish without error
        n_samples = X.shape[0]
        n_components = dictionary.shape[0]
        return np.zeros((n_samples, n_components))

    # 4-atom dictionary over 3 features
    rng = np.random.RandomState(0)
    dictionary = rng.randn(4, 3)
    coder = SparseCoder(
        dictionary=dictionary,
        transform_algorithm=algorithm,
        transform_n_nonzero_coefs=n_nonzero_coefs,
        transform_alpha=alpha,
        split_sign=False,
        n_jobs=n_jobs,
        positive_code=positive,
        transform_max_iter=max_iter,
    )
    X = rng.randn(2, 3)
    dl.sparse_encode = spy
    try:
        coder.transform(X)
    finally:
        dl.sparse_encode = real_sparse_encode
    return (
        ALGO_CODE[captured.get("algorithm")],
        captured.get("n_nonzero_coefs"),
        captured.get("alpha"),
        captured.get("max_iter"),
        captured.get("n_jobs"),
        captured.get("positive"),
    )


# --- SHADOW of implementation_codingSolverArgs (the R/I leg) -----------------
# Mirrors Solution.lean: record each option, then read it back into the bundle.
def shadow_args(algorithm, n_nonzero_coefs, alpha, n_jobs, positive, max_iter):
    cfg = {
        "algorithm": ALGO_CODE[algorithm],
        "n_nonzero_coefs": n_nonzero_coefs,
        "alpha": alpha,
        "n_jobs": n_jobs,
        "positive": positive,
        "max_iter": max_iter,
    }
    return (
        cfg["algorithm"],
        cfg["n_nonzero_coefs"],
        cfg["alpha"],
        cfg["max_iter"],
        cfg["n_jobs"],
        cfg["positive"],
    )


def disagree(args):
    got = oracle_args(*args)
    want = shadow_args(*args)
    if got != want:
        return (args, got, want)
    return None


NNZ_POOL = [None, 1, 2, 3]
ALPHA_POOL = [None, 0.1, 1.0, 5.0]
NJOBS_POOL = [None, 1, 2]


def _enumerate_edge():
    cases = []
    # the F2P shape: lasso_cd with a tight then loose iteration budget
    cases.append(("lasso_cd", None, None, None, False, 1))
    cases.append(("lasso_cd", None, None, None, False, 2000))
    cases.append(("lasso_lars", None, None, None, False, 1))
    cases.append(("lasso_lars", None, None, None, False, 1000))
    for algo in ALGOS:
        cases.append((algo, None, None, None, False, 1000))
        cases.append((algo, 2, 1.0, 1, True, 50))
    return cases


def main() -> int:
    checked = 0
    for args in _enumerate_edge():
        d = disagree(args)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        args = (
            rng.choice(ALGOS),
            rng.choice(NNZ_POOL),
            rng.choice(ALPHA_POOL),
            rng.choice(NJOBS_POOL),
            rng.choice([True, False]),
            rng.randint(1, 5000),
        )
        d = disagree(args)
        if d:
            print(f"DISAGREE fuzz {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
