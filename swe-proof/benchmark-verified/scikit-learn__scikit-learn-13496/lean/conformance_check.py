#!/usr/bin/env python3
"""G-CONF for scikit-learn__scikit-learn-13496.

The gold patch is already applied to /testbed when this runs (so
`IsolationForest.__init__` accepts and forwards `warm_start`). We compare the
R/I Python shadow of `implementation_isolationForestInit` (the Lean impl,
transliterated op-for-op per refinement.md) against the REAL patched constructor:
build `IsolationForest(**kwargs)` and read back the stored configuration
attributes. Over >=1e5 fuzzed configurations, zero disagreements => exit 0.

Type bijection (mapping.md):
  warmStart, bootstrap            : bool  <->  Bool
  bootstrapFeatures (always False), oobScore (always False) : bool fixed defaults
  nEstimators, verbose            : int   <->  Nat (non-negative)
  behaviour                       : str   <->  String
  maxSamples, contamination, maxFeatures, nJobs, randomState : pass-through values
                                                (stored by identity; opaque type vars)

stdlib + sklearn only.
"""
import random
import sys
import warnings

warnings.filterwarnings("ignore")

from sklearn.ensemble import IsolationForest

SEED = 13496
N = 120_000  # >= 10^5

# The attributes the constructor stores (mapping.md). Each must equal what the
# shadow stores by identity.
ATTRS = [
    "n_estimators", "max_samples", "contamination", "max_features",
    "bootstrap", "bootstrap_features", "oob_score", "warm_start",
    "n_jobs", "behaviour", "random_state", "verbose",
]


def shadow(kw):
    """R/I shadow of implementation_isolationForestInit: store every supplied
    parameter by identity; bootstrap_features and oob_score are fixed off."""
    return {
        "n_estimators": kw["n_estimators"],
        "max_samples": kw["max_samples"],
        "contamination": kw["contamination"],
        "max_features": kw["max_features"],
        "bootstrap": kw["bootstrap"],
        "bootstrap_features": False,
        "oob_score": False,
        "warm_start": kw["warm_start"],
        "n_jobs": kw["n_jobs"],
        "behaviour": kw["behaviour"],
        "random_state": kw["random_state"],
        "verbose": kw["verbose"],
    }


def oracle(kw):
    """Real patched constructor: instantiate and read back stored attributes."""
    clf = IsolationForest(**kw)
    return {a: getattr(clf, a) for a in ATTRS}


def gen(rng):
    return {
        "n_estimators": rng.randint(0, 1000),
        "max_samples": rng.choice(["auto", rng.random(), rng.randint(1, 100)]),
        "contamination": rng.choice(["legacy", "auto", rng.random()]),
        "max_features": rng.choice([rng.random(), rng.randint(1, 10)]),
        "bootstrap": rng.choice([True, False]),
        "n_jobs": rng.choice([None, rng.randint(1, 8), -1]),
        "behaviour": rng.choice(["old", "new", "deprecated"]),
        "random_state": rng.choice([None, rng.randint(0, 2**31 - 1)]),
        "verbose": rng.randint(0, 5),
        "warm_start": rng.choice([True, False]),
    }


def main():
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    # Deterministic boundary cases first: both warm_start polarities and the
    # default-ish config the F2P test exercises.
    fixed = [
        {"n_estimators": 10, "max_samples": 20, "contamination": "legacy",
         "max_features": 1.0, "bootstrap": False, "n_jobs": None,
         "behaviour": "old", "random_state": 0, "verbose": 0,
         "warm_start": True},
        {"n_estimators": 100, "max_samples": "auto", "contamination": "legacy",
         "max_features": 1.0, "bootstrap": False, "n_jobs": None,
         "behaviour": "old", "random_state": None, "verbose": 0,
         "warm_start": False},
    ]
    cases = fixed + [gen(rng) for _ in range(N)]

    for kw in cases:
        got = shadow(kw)
        want = oracle(kw)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((kw, got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for kw, g, w in examples:
            diff = {k: (g[k], w[k]) for k in ATTRS if g[k] != w[k]}
            print(f"  in={kw} diff(shadow,real)={diff}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
