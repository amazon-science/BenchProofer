#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-12973
(nagini).

SHADOW: the impl region of model.py, copied VERBATIM below with the contract
calls stripped (the impl region itself contains none — no Requires/Ensures/
Invariant/Assert live inside it). The @Pure helper `selected_preference`
copies over as a plain function. The carriers `Estimator` / `InputArray` are
minimal attribute holders and are reproduced as plain classes; there is no
PSeq usage and no @ContractOnly callee in this bundle.

ORACLE: the REAL patched repo method the model models per mapping.md —
`sklearn.linear_model.LassoLarsIC.fit` (the gate applies patch.diff to
/testbed before this script runs; PYTHONPATH=/testbed resolves the patched
in-tree source). The estimator is constructed with the candidate
construction-time copy preference, `fit` is called with (or without) the
per-call preference, and the observable is whether the training array is
left byte-for-byte intact afterwards: `np.array_equal(X, X_copy_before)`.

TYPE BRIDGE (mapping.md section 2):
  - `Estimator.default_copy : bool`  <-> the estimator's construction-time
    copy preference (identity on the bool).
  - `copy_X : Optional[bool]`        <-> the per-call preference; model None
    ("caller supplied nothing") is exercised BOTH as an omitted argument and
    as an explicitly-passed unset value — the two real framings of "unset".
  - `InputArray.native_format : bool`<-> whether the supplied X is already in
    the routine's native numeric working representation (an accepted float
    dtype), so input validation does NOT have to materialize a converted
    working copy. True is realized with a float64 array; False with an
    integer-dtype array (validation must convert, shielding the caller's
    array).
  - `InputArray.intact : bool`       <-> `np.array_equal(X, X_copy)` after
    fit (True iff the array was preserved; beyond the dtype-nativeness bit
    the array's contents/shape are irrelevant to this bool and are therefore
    fuzzed freely on the real side without changing the model input).
  - the shadow's return value        <-> the preference that governed
    preprocessing; its real observable is the intact bool joined with the
    nativeness bit (intact == (return or not native_format), asserted below).

INPUT DOMAIN: the preconditions demand only field permissions, so every
(default_copy in {True, False}, per_call in {True, False, None},
native_format in {True, False}) triple is Requires-satisfying — a 12-point
semantic domain (the model abstracts the rest of the array away). >= 1e5
inputs are drawn over it: boundary = the full cross product x {omitted,
explicit-unset} framings x several fresh data draws, each against a REAL fit
execution; fuzz = 100000 draws, each diffed against the oracle verdict for
that semantic point, where the oracle verdict is (re)established by a REAL
fit execution with fresh random data on every 50th draw (~2000 real
executions spread over the stream) and memoized in between — the
memoized-oracle pattern used by other finite-domain bundles.

Pinned fuzz seed: 129730. Exit 0 iff zero disagreements; on disagreement
prints the input and both outputs and exits 1. stdlib + numpy + sklearn
(the repo under test) only.
"""
import json
import random
import sys

import numpy as np


SEED = 129730
N_FUZZ = 100_000
REAL_EVERY = 50          # every 50th fuzz draw re-runs the REAL fit


# --- pure helper from model.py, decorator stripped ----------------------------

def selected_preference(default_copy, per_call):
    """The preference that governs preprocessing: the per-call preference if the
    caller supplied one (not ``None``), otherwise the construction-time default."""
    if per_call is None:
        return default_copy
    return per_call


# --- carrier shims (plain attribute holders, contracts stripped) ---------------

class Estimator:
    def __init__(self, default_copy):
        self.default_copy = default_copy


class InputArray:
    def __init__(self, intact, native_format):
        self.intact = intact
        self.native_format = native_format


# --- the impl region of model.py, VERBATIM -------------------------------------

def fit_shadow(config, data, copy_X):
    if copy_X is None:
        copy_X = config.default_copy
    effective = copy_X  # governs both preprocessing and the fitting routine
    if data.native_format:
        data.intact = effective
    else:
        data.intact = True
    return effective


# --- oracle: the REAL patched estimator ----------------------------------------

def real_intact(LassoLarsIC, init_copy_X, fit_copy_X, native, omit_when_none,
                rng):
    """Run the REAL LassoLarsIC.fit with fresh random data and report whether
    the training array X is left intact (== its content before fit). Model
    None is framed either as an omitted argument or as an explicitly-passed
    unset value, per `omit_when_none`. `native` selects whether X is supplied
    already in the routine's native float working dtype (float64) or in a
    non-native dtype (int64) that validation must convert."""
    est = LassoLarsIC(copy_X=init_copy_X, precompute=False)
    n_samples = rng.randint(30, 120)
    n_features = rng.randint(3, 8)
    X = np.random.RandomState(rng.randint(0, 2**31 - 1)).normal(
        0, 1, (n_samples, n_features))
    if not native:
        X = (X * 10).astype(np.int64)
    X_copy = X.copy()
    y = X[:, rng.randint(0, n_features - 1)].astype(np.float64)
    if fit_copy_X is None and omit_when_none:
        est.fit(X, y)
    else:
        est.fit(X, y, copy_X=fit_copy_X)
    return bool(np.array_equal(X, X_copy))


def diff_one(shadow_config_default, per_call, native, oracle_intact):
    """Diff the shadow against one real observation. Returns None on
    agreement, else a diagnostic string."""
    config = Estimator(shadow_config_default)
    data = InputArray(True, native)
    result = fit_shadow(config, data, per_call)
    # internal consistency: intact == (return or not native_format)
    assert data.intact == (result or not data.native_format)
    # frame conditions of the model: config default + format flag untouched
    assert config.default_copy == shadow_config_default
    assert data.native_format == native
    if data.intact != oracle_intact:
        return ("DISAGREEMENT\n"
                "  default_copy=%r per_call=%r native_format=%r\n"
                "  shadow: intact=%r (return=%r)\n"
                "  real:   X left intact=%r"
                % (shadow_config_default, per_call, native, data.intact,
                   result, oracle_intact))
    return None


def main():
    from sklearn.linear_model import LassoLarsIC

    rng = random.Random(SEED)
    combos = [(d, p, n) for d in (True, False) for p in (True, False, None)
              for n in (True, False)]
    checked = 0
    real_runs = 0

    # --- boundary: full cross product x both None framings x fresh data ------
    for init_copy_X, fit_copy_X, native in combos:
        for omit in (True, False):
            for _ in range(5):
                intact = real_intact(LassoLarsIC, init_copy_X, fit_copy_X,
                                     native, omit, rng)
                real_runs += 1
                err = diff_one(init_copy_X, fit_copy_X, native, intact)
                if err:
                    print(err)
                    return 1
                checked += 1
    n_boundary = checked

    # --- fuzz: 1e5 draws over the semantic domain; memoized oracle refreshed
    # --- by a REAL execution (fresh data, alternating None framing) every
    # --- REAL_EVERY draws --------------------------------------------------
    oracle_cache = {}
    for i in range(N_FUZZ):
        init_copy_X = rng.choice([True, False])
        fit_copy_X = rng.choice([True, False, None])
        native = rng.choice([True, False])
        key = (init_copy_X, fit_copy_X, native)
        if key not in oracle_cache or i % REAL_EVERY == 0:
            omit = rng.random() < 0.5
            oracle_cache[key] = real_intact(LassoLarsIC, init_copy_X,
                                            fit_copy_X, native, omit, rng)
            real_runs += 1
        err = diff_one(init_copy_X, fit_copy_X, native, oracle_cache[key])
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real fitting routine on %d inputs "
          "(%d boundary + %d fuzz over the 12-point semantic domain; "
          "%d REAL fit executions; seed %d)."
          % (checked, n_boundary, N_FUZZ, real_runs, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "real_executions": real_runs,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
