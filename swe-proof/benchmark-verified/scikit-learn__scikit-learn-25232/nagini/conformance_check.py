#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-25232
(nagini).

SHADOW: the impl region of model.py, copied VERBATIM below with contract
calls stripped (the impl region contains none - no Requires/Ensures/
Invariant/Assert live inside it). The one @ContractOnly callee,
`constant_statistics`, is bridged to the REAL repo function it axiomatizes
per mapping.md section 3.1: the single-pass imputer's constant strategy
(`sklearn.impute.SimpleImputer(strategy="constant")` fitted on numerical
data, reading `statistics_`). That callee is deterministic in
(requested, n_features) for numerical data, so the bridge memoizes its
real executions per exact argument pair. There is no PSeq usage and no
@Pure helper consumed by the impl region.

ORACLE: the REAL patched repo behaviour the model models per mapping.md /
refinement.md - the iterative imputer's first-round constant
initialization: fit `sklearn.impute.IterativeImputer(
initial_strategy="constant", fill_value=<requested>, max_iter=0)` on
numerical data with `n_features` columns and read
`initial_imputer_.statistics_`. The gate applies patch.diff to /testbed
before this script runs; PYTHONPATH=/testbed resolves the patched in-tree
source (the pre-patch import would reject the keyword outright).

TYPE BRIDGE (mapping.md section 2):
  - `requested : Optional[int]` <-> the estimator's optional replacement
    value (None-or-numerical). Model None is exercised BOTH as an omitted
    keyword and as an explicitly-passed unset value - the two real framings
    of "unset". Integer carriers are exact in float64 well past the fuzz
    range used here, so int <-> float equality is precision-free.
  - `n_features : int` <-> `X.shape[1]` of the fitted data. The model's
    precondition admits n_features == 0, but no real fit exists for
    zero-column data (array validation rejects it), so the executable
    domain is n_features >= 1; the n_features == 0 point is degenerate
    (the postcondition's per-feature clause is vacuous there).
  - `List[int]` result <-> the installed per-feature constant ndarray;
    element j <-> index j, len <-> shape[0], exact numeric equality.

INPUT DOMAIN: every (requested in Optional[int], n_features >= 1) pair is
Requires-satisfying. The pool is boundary values (None, 0, +/-1, +/-2, 7,
42, +/-100, 999, -999, +/-10**6, 2**31-1, ...) plus 200 seeded random ints
in [-10**9, 10**9], crossed with feature counts {1..16, 32}. Every pool key
gets a REAL IterativeImputer execution (fresh random data per key); the
>= 1e5 fuzz draws are then diffed shadow-vs-oracle over the pool. Data
contents/shape beyond the column count are irrelevant to the observable
(uniform constant array) and are fuzzed freely on the real side.

Pinned fuzz seed: 252320. Exit 0 iff zero disagreements; on disagreement
prints the input and both outputs and exits 1. stdlib + numpy + sklearn
(the package under test) only.
"""
import json
import random
import sys

import numpy as np

SEED = 252320
N_FUZZ = 100_000


# --- bridge for the @ContractOnly callee: the REAL single-pass imputer ---------
# Deterministic in (requested, n_features) on numerical data, so real
# executions are memoized per exact argument pair.

_SIMPLE_CACHE = {}


def make_constant_statistics(SimpleImputer, rng):
    def constant_statistics(requested, n_features):
        key = (requested, n_features)
        if key not in _SIMPLE_CACHE:
            X = np.random.RandomState(rng.randint(0, 2**31 - 1)).normal(
                0.0, 5.0, (5, n_features))
            X[0, :] = np.nan  # ensure there is something to fill
            kwargs = {"strategy": "constant"}
            if requested is not None:
                kwargs["fill_value"] = requested
            imp = SimpleImputer(**kwargs)
            imp.fit(X)
            _SIMPLE_CACHE[key] = list(imp.statistics_)
        return list(_SIMPLE_CACHE[key])
    return constant_statistics


# --- the impl region of model.py, VERBATIM (contracts stripped: none inside) ---

def make_shadow(constant_statistics):
    def initial_constant_fill(requested, n_features):
        # impl region body:
        statistics = constant_statistics(requested, n_features)
        return statistics
    return initial_constant_fill


# --- oracle: the REAL patched iterative imputer --------------------------------

def real_initial_constants(IterativeImputer, requested, n_features,
                           omit_when_none, rng):
    """Fit the REAL IterativeImputer with a first-round constant
    initialization on fresh random numerical data with n_features columns
    and return the installed per-feature constant array. Model None is
    framed either as an omitted keyword or as an explicitly-passed unset
    value, per omit_when_none."""
    n_samples = rng.randint(4, 9)
    X = np.random.RandomState(rng.randint(0, 2**31 - 1)).normal(
        0.0, 5.0, (n_samples, n_features))
    X[0, :] = np.nan  # ensure there is something to fill
    kwargs = {"initial_strategy": "constant", "max_iter": 0}
    if requested is None and omit_when_none:
        pass
    else:
        kwargs["fill_value"] = requested
    imp = IterativeImputer(**kwargs)
    imp.fit_transform(X)
    return list(imp.initial_imputer_.statistics_)


def diff_one(shadow, requested, n_features, oracle_stats):
    """Diff the shadow against one real observation. Returns None on
    agreement, else a diagnostic string."""
    result = shadow(requested, n_features)
    ok = (len(result) == len(oracle_stats)
          and all(float(result[j]) == float(oracle_stats[j])
                  for j in range(len(result))))
    if not ok:
        return ("DISAGREEMENT\n"
                "  requested=%r n_features=%r\n"
                "  shadow: %r\n"
                "  real:   %r"
                % (requested, n_features, result, oracle_stats))
    return None


def main():
    import warnings
    warnings.filterwarnings("ignore")
    from sklearn.experimental import enable_iterative_imputer  # noqa: F401
    from sklearn.impute import IterativeImputer, SimpleImputer

    rng = random.Random(SEED)
    shadow = make_shadow(make_constant_statistics(SimpleImputer, rng))

    boundary_values = [None, 0, 1, -1, 2, -2, 7, 42, 100, -100, 999, -999,
                       10**6, -10**6, 2**31 - 1, -(2**31 - 1)]
    fuzz_values = [rng.randint(-10**9, 10**9) for _ in range(200)]
    requested_pool = boundary_values + fuzz_values
    feature_pool = list(range(1, 17)) + [32]

    checked = 0
    real_runs = 0

    # --- boundary + oracle precompute: one REAL iterative-imputer execution
    # --- per (requested, n_features) key; None additionally exercised in
    # --- both unset framings, asserted to agree -----------------------------
    oracle = {}
    for req in requested_pool:
        for n in feature_pool:
            stats = real_initial_constants(IterativeImputer, req, n, True, rng)
            real_runs += 1
            if req is None:
                stats2 = real_initial_constants(IterativeImputer, req, n,
                                                False, rng)
                real_runs += 1
                if stats != stats2:
                    print("ORACLE FRAMING MISMATCH on requested=None "
                          "n_features=%d: omitted=%r explicit=%r"
                          % (n, stats, stats2))
                    return 1
            oracle[(req, n)] = stats
            err = diff_one(shadow, req, n, stats)
            if err:
                print(err)
                return 1
            checked += 1
    n_boundary = checked

    # --- fuzz: >= 1e5 draws over the pool, each diffed against the
    # --- precomputed real-oracle value for that exact input ----------------
    for _ in range(N_FUZZ):
        req = rng.choice(requested_pool)
        n = rng.choice(feature_pool)
        err = diff_one(shadow, req, n, oracle[(req, n)])
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real first-round constant "
          "initialization on %d inputs (%d boundary keys + %d fuzz draws; "
          "%d REAL iterative-imputer executions, %d REAL single-pass "
          "bridge executions; seed %d)."
          % (checked, n_boundary, N_FUZZ, real_runs, len(_SIMPLE_CACHE),
             SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "real_executions": real_runs,
                      "bridge_executions": len(_SIMPLE_CACHE),
                      "shadow": "direct (contract-stripped impl region; "
                                "@ContractOnly callee bridged to the real "
                                "single-pass imputer)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
