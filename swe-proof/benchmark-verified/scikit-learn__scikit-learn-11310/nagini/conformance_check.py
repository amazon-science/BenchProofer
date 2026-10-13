#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-11310
(nagini).

SHADOW: the impl region of model.py, copied VERBATIM below with the contract
calls stripped (the Requires/Ensures lines; the impl body itself carries no
contract calls). There are no @Pure helper functions in this bundle. The two
@ContractOnly axiom callees realize as the REAL operations they model per
mapping.md section 3:

  * `elapsed_between(earlier, later)` models the builtin float subtraction of
    two ordered readings, so the shadow callee IS `later - earlier`;
  * `clock_after` models the stdlib wall-clock reading; the proof abstracts
    its two reads as the ordered inputs (start, end), so it has no call site
    in the impl region — it grounds the input domain (`end >= start`) instead,
    which is exactly how this script generates inputs.

ORACLE: the REAL patched repo behaviour the model models per mapping.md — the
refit branch of `BaseSearchCV.fit` (exercised through `GridSearchCV`),
imported from /testbed (the gate applies patch.diff before this script runs;
PYTHONPATH=/testbed). To drive the model's (start, end) inputs through the
real code path, the module-level timer that branch reads is swapped for a
scripted stand-in that returns the two pinned readings in order (and falls
back to the real timer if anything else were to read it — nothing does; a
stray consumption would surface as a huge reading and a disagreement). The
observed outcome is the estimator's recorded-duration attribute
(`refit_time_`): its presence/absence and, when present, its exact float
value.

Type bridge (mapping.md section 2):
  do_final_fit : bool        <-> the `refit` constructor argument (True/False;
                                 the branch guard is plain truthiness, and the
                                 modeled carrier is that truth value)
  start, end   : float       <-> the two scripted timer readings the branch
                                 takes, in order (end >= start: the modeled
                                 timer monotonicity — the generated domain)
  Result()     : Optional[float] <-> attribute present with value v ==
                                 Result() == v; attribute absent ==
                                 Result() is None

The comparison is exact: the shadow computes the same builtin float
subtraction over the same two floats the oracle's branch receives, so any
value discrepancy is a genuine behavioural disagreement, not float noise.

Input domain: Requires(end >= start). Boundary cases cover the zero-length
interval, denormal/tiny/huge intervals, negative and epoch-scale readings —
each crossed with both do_final_fit values; fuzz draws ordered pairs over
[-1e12, 1e12] plus epoch-scale base+delta pairs, with do_final_fit drawn per
case. A small unscripted supplement runs the branch under the REAL timer and
checks the presence bijection and the non-negative-float consequence (the
exact readings are unobservable there, so only presence/type/sign compare).

>= 1e5 Requires-satisfying inputs: 28 boundary + 100000 fuzz (+200
real-timer supplement, not counted). Pinned fuzz seed: 11310.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + numpy + the repo under test only.
"""
import json
import random
import sys
import time as _real_time
import warnings

import numpy as np

SEED = 11310
N_FUZZ = 100_000
N_REAL_TIMER = 200

warnings.simplefilter("ignore")

import sklearn.model_selection._search as search_mod
from sklearn.base import BaseEstimator


# --- @ContractOnly axiom callee, realized as the REAL operation it models ----

def elapsed_between(earlier, later):
    # mapping.md section 3.2: this axiom models the builtin float subtraction
    # of the later reading minus the earlier one — the real operation.
    return later - earlier


# --- the impl region of model.py, verbatim, contract calls stripped ----------

def recorded_refit_duration(do_final_fit, start, end):
    result = None  # type: ignore
    if do_final_fit:
        # the elapsed interval is the later reading minus the earlier one; the
        # readings are ordered (end >= start), so the interval is a non-negative
        # real value.
        result = elapsed_between(start, end)
    return result


# --- oracle harness -----------------------------------------------------------

class _TinyEstimator(BaseEstimator):
    """Minimal fittable/scorable estimator so the search's final fit is cheap;
    the modeled behaviour is independent of what the fit computes."""

    def __init__(self, p=0):
        self.p = p

    def fit(self, X, y=None):
        return self

    def score(self, X, y=None):
        return 0.0


class _ScriptedClock(object):
    """Stands in for the module-level timer during one oracle run: hands out
    the pinned readings in order, then falls back to the real timer (nothing
    else in that module reads the timer, and a stray consumption would show
    up as an epoch-scale reading and a value disagreement)."""

    def __init__(self):
        self.readings = []

    def time(self):
        if self.readings:
            return self.readings.pop(0)
        return _real_time.time()


X_DATA = np.zeros((4, 1))
Y_DATA = np.array([0, 1, 0, 1])

_clock = _ScriptedClock()
# Swap the module-level timer the branch under test reads for the scripted
# stand-in (empty script => real timer, so unscripted runs behave normally).
search_mod.time = _clock


def oracle(do_final_fit, start, end, scripted=True):
    """Run the REAL search fit once; return the recorded duration (or None if
    the attribute is absent) plus the number of scripted readings consumed."""
    gs = search_mod.GridSearchCV(_TinyEstimator(), {"p": [0]}, cv=2,
                                 refit=do_final_fit)
    if scripted:
        _clock.readings = [start, end]
        before = 2
    else:
        _clock.readings = []
        before = 0
    gs.fit(X_DATA, Y_DATA)
    consumed = before - len(_clock.readings)
    _clock.readings = []
    present = hasattr(gs, "refit_time_")
    return (gs.refit_time_ if present else None), consumed


def fail(kind, do_final_fit, start, end, shadow_res, real_res):
    print("DISAGREEMENT (%s)\n  do_final_fit=%r start=%r end=%r\n"
          "  shadow=%r\n  real=%r"
          % (kind, do_final_fit, start, end, shadow_res, real_res))
    return True


def check_case(do_final_fit, start, end):
    """Diff shadow vs oracle on one Requires-satisfying input; True on
    disagreement."""
    assert end >= start  # Requires holds by construction
    shadow_res = recorded_refit_duration(do_final_fit, start, end)
    real_res, consumed = oracle(do_final_fit, start, end)
    expected_consumed = 2 if do_final_fit else 0
    if consumed != expected_consumed:
        return fail("timer reads: consumed %d, expected %d"
                    % (consumed, expected_consumed),
                    do_final_fit, start, end, shadow_res, real_res)
    if (shadow_res is None) != (real_res is None):
        return fail("presence", do_final_fit, start, end, shadow_res, real_res)
    if shadow_res is not None:
        if not isinstance(real_res, float):
            return fail("type: real result not a float",
                        do_final_fit, start, end, shadow_res, real_res)
        if not (shadow_res == real_res):
            return fail("value", do_final_fit, start, end, shadow_res, real_res)
    return False


def boundary_pairs():
    return [
        (0.0, 0.0),                       # zero-length interval
        (-0.0, 0.0),
        (0.0, 5e-324),                    # smallest positive interval
        (0.0, 1e-9),
        (1.0, 1.0),
        (-1.0, 0.0),                      # negative readings, still ordered
        (-5.0, -1.0),
        (1234567890.0, 1234567890.5),     # epoch-scale readings
        (1.5e9, 1.5e9 + 0.25),
        (0.0, 1e18),                      # very large interval
        (1e18, 1e18),
        (-1e18, 1e18),
        (5e-324, 5e-324),
        (3.140625, 3.15625),
    ]


def main():
    checked = 0

    # --- boundary: every pair x both branch decisions -------------------------
    n_boundary = 0
    for start, end in boundary_pairs():
        for do_final_fit in (True, False):
            if check_case(do_final_fit, start, end):
                return 1
            checked += 1
            n_boundary += 1

    # --- fuzz: pinned seed ----------------------------------------------------
    rng = random.Random(SEED)
    for i in range(N_FUZZ):
        do_final_fit = rng.random() < 0.5
        if rng.random() < 0.25:
            # epoch-scale base + small delta: the shape real readings take
            base = rng.uniform(1e9, 2e9)
            start = base
            end = base + rng.uniform(0.0, 10.0)
        else:
            x = rng.uniform(-1e12, 1e12)
            y = rng.uniform(-1e12, 1e12)
            start, end = (x, y) if x <= y else (y, x)
        if check_case(do_final_fit, start, end):
            return 1
        checked += 1

    # --- supplement: the REAL timer, unscripted (presence/type/sign only) ----
    for i in range(N_REAL_TIMER):
        do_final_fit = (i % 2 == 0)
        real_res, _ = oracle(do_final_fit, 0.0, 0.0, scripted=False)
        if do_final_fit != (real_res is not None):
            print("DISAGREEMENT (real-timer presence)\n  do_final_fit=%r\n"
                  "  real=%r" % (do_final_fit, real_res))
            return 1
        if real_res is not None and not (isinstance(real_res, float)
                                         and real_res >= 0.0):
            print("DISAGREEMENT (real-timer result not a non-negative float)\n"
                  "  real=%r" % (real_res,))
            return 1

    print("G-CONF OK: shadow impl == real search refit-duration recording on "
          "%d inputs (%d boundary + %d fuzz, seed %d; +%d real-timer "
          "supplement runs)."
          % (checked, n_boundary, N_FUZZ, SEED, N_REAL_TIMER))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region; "
                                "axiom callee = the real float subtraction)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
