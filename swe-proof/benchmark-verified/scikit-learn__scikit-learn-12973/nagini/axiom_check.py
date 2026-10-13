#!/usr/bin/env python3
"""G-AX executable soundness check for scikit-learn__scikit-learn-12973.

This bundle consumes NO @ContractOnly axiom: the changed behaviour is a boolean
dataflow (which copy preference governs preprocessing, and its consequence for
the input array) and is modeled DEEPLY in model.py. G-AX therefore validates
that deep boolean model (the A-reference) against the REAL estimator.

The deep model (model.py):
  selected_preference(default_copy, per_call) = per_call if per_call is not None
                                                else default_copy
  InputArray.intact == (selected_preference(default_copy, per_call)
                        or not native_format)
i.e. after fitting, the input array is left byte-for-byte intact IFF the
selected copy preference is True OR the array was not already in the routine's
native float working dtype (in which case input validation materializes a
converted working copy, shielding the caller's array regardless of the flag).

This script executes the REAL post-fix `LassoLarsIC.fit` (the same scikit-learn
install the gold patch lands in, in-container) over the boundary + fuzzed cross
product of (construction-time copy_X, per-call fit copy_X, input dtype
nativeness) and asserts:

    np.array_equal(X, X_copy_before_fit)  ==  (selected_preference(init_copy_X,
                                                                   fit_copy_X)
                                               or not native)

The native=True points are exactly what the F2P tests observe
(`test_lasso_lars_fit_copyX_behaviour`, `test_lasso_lars_copyX_behaviour`);
the native=False points pin the conversion-shield disjunct.

Imports are stdlib (`random`, `sys`) plus `numpy` and `sklearn` — i.e. the very
library whose method the gold patch edits; nothing repo-test-specific. Exit 0
iff every observation matches the deep model.

Run in the evaluation container AFTER the gold patch is applied (the soundness
claim is that the deep model == the fixed real callee). On the pre-patch tree
the native=True, `fit_copy_X is not None` cases legitimately disagree — that
disagreement is the bug the spec senses (G-DIFF), not an axiom_check failure.
"""
import random
import sys

import numpy as np
from sklearn.linear_model import LassoLarsIC


# --- model.py reference encoding (kept in lock-step with the deep model) -----

def selected_preference(default_copy, per_call):
    """Reference of model.py's `selected_preference`: the per-call preference if
    the caller supplied one (not None), else the construction-time default."""
    if per_call is None:
        return default_copy
    return per_call


# --- the check ---------------------------------------------------------------

def observe_real_fit(init_copy_X, fit_copy_X, native, rng):
    """Run the REAL LassoLarsIC.fit and report whether the input array X is left
    intact (== its content before fit), i.e. the real `np.array_equal(X,X_copy)`
    the F2P tests read. `native` selects float64 (native working dtype) vs
    int64 (validation must materialize a converted working copy) input."""
    lasso_lars = LassoLarsIC(copy_X=init_copy_X, precompute=False)
    X = rng.normal(0, 1, (100, 5))
    if not native:
        X = (X * 10).astype(np.int64)
    X_copy = X.copy()
    y = X[:, 2].astype(np.float64)
    if fit_copy_X is None:
        lasso_lars.fit(X, y)               # caller supplies no per-call value
    else:
        lasso_lars.fit(X, y, copy_X=fit_copy_X)
    return np.array_equal(X, X_copy)       # True iff X was left intact


def check(init_copy_X, fit_copy_X, native, rng):
    intact = observe_real_fit(init_copy_X, fit_copy_X, native, rng)
    expected = selected_preference(init_copy_X, fit_copy_X) or not native
    assert intact == expected, (
        "deep model unsound for init_copy_X=%r fit_copy_X=%r native=%r: real "
        "fit left X intact=%r, deep model expects=%r"
        % (init_copy_X, fit_copy_X, native, intact, expected))


def main():
    rng = np.random.RandomState(0)

    # --- boundary: full cross product {T,F} x {T,F,None} x {T,F} -------------
    combos = [(i, f, n) for i in (True, False) for f in (True, False, None)
              for n in (True, False)]
    for init_copy_X, fit_copy_X, native in combos:
        check(init_copy_X, fit_copy_X, native, rng)

    # --- fuzz: repeat each combo with fresh random data --------------------
    pyrng = random.Random(12973)
    for _ in range(200):
        init_copy_X = pyrng.choice([True, False])
        fit_copy_X = pyrng.choice([True, False, None])
        native = pyrng.choice([True, False])
        check(init_copy_X, fit_copy_X, native, rng)

    print("G-AX OK: deep boolean model (selected_preference / intact modulo "
          "format conversion) == real LassoLarsIC.fit on %d boundary combos + "
          "200 fuzz runs (np.array_equal(X, X_copy) matches in every case)"
          % len(combos))
    return 0


if __name__ == "__main__":
    sys.exit(main())
