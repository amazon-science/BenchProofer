#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-26194
(nagini).

SHADOW  — the impl region of model.py (`anchor_thresholds`), copied VERBATIM
          with the contract calls (Requires/Ensures/Invariant and their
          Acc/list_pred arguments) stripped; the model IS Python, so no
          transliteration. The one @ContractOnly callee the impl uses,
          `pos_inf()`, calls the REAL repo primitive it models (`numpy.inf`,
          mapping.md §3.1). `is_pos_inf` appears only inside stripped
          contract lines, so no shim for it is needed.

BRIDGE  — mapping.md §2's type abstraction: the repo-side 1-D float ndarray
          of descending distinct finite scores ↔ `List[float]`
          (element k ↔ element k, len ↔ len). ndarray → list(float) on the
          way in; the shadow's output list is compared elementwise against
          the oracle's output array.

ORACLE  — the REAL patched repo function under specification:
          `sklearn.metrics.roc_curve` (PYTHONPATH=/testbed, gold patch
          applied by the gate before this script runs). The modeled step is
          the final threshold-anchoring tail of roc_curve, whose input is
          the threshold array produced by the unchanged upstream helper
          `_binary_clf_curve` (mapping.md §1). So for each fuzzed
          (y_true, y_score) pair we obtain the shadow's input by calling the
          real unchanged `_binary_clf_curve` (with the intermediate-dropping
          option off, that array feeds the anchoring step directly), run the
          shadow on it, and diff against the full real
          `roc_curve(..., drop_intermediate=False)` thresholds.
          A second leg covers drop_intermediate=True: there the pruned
          pre-anchoring array is by construction the tail of the real
          output, so the shadow run on that tail must reproduce the real
          output exactly (this pins the leading element and the length on
          the pruned path too).

Exit 0 iff zero disagreements over the boundary cases + 100000 fuzzed
Requires-satisfying inputs (each input is a non-empty threshold list,
satisfying `len(thresholds) >= 1`). Pinned seed: 2619400. stdlib + numpy.
"""
import random
import sys

import numpy as np
from sklearn.metrics import roc_curve
from sklearn.metrics._ranking import _binary_clf_curve

SEED = 2619400
N_FUZZ = 100_000


# ---------------------------------------------------------------------------
# @ContractOnly callee shim: calls the REAL repo primitive it models
# (mapping.md §3.1 — the positive-infinity sentinel is numpy.inf).
# ---------------------------------------------------------------------------

def pos_inf():
    return np.inf


# ---------------------------------------------------------------------------
# model.py impl region, VERBATIM with contract statement lines
# (Requires/Ensures/Invariant) stripped.
# ---------------------------------------------------------------------------

def anchor_thresholds(thresholds):
    lead = pos_inf()
    result = [lead]  # type: list
    i = 0
    while i < len(thresholds):
        result.append(thresholds[i])
        i = i + 1
    return result


# ---------------------------------------------------------------------------
# Bridge + comparison helpers
# ---------------------------------------------------------------------------

def as_model_list(arr):
    """ndarray of float -> List[float] (mapping.md §2 bijection)."""
    return [float(v) for v in arr]


def lists_equal(a, b):
    if len(a) != len(b):
        return False
    for x, y in zip(a, b):
        # exact real-number identity; covers the infinite sentinel too
        # (inf == inf) and the inputs are finite/distinct so no NaN arises
        if not (x == y):
            return False
    return True


# ---------------------------------------------------------------------------
# Input generation: (y_true, y_score) pairs whose derived threshold arrays
# are Requires-satisfying (non-empty) and range over score scales: unit
# interval probabilities, arbitrary confidences, large magnitudes, extremes,
# ties, and the single-distinct-score edge.
# ---------------------------------------------------------------------------

def boundary_cases():
    yield ([0, 1], [0.1, 0.9])                          # probability estimates
    yield ([0, 0, 1, 1], [0.1, 0.4, 0.35, 0.8])
    yield ([0, 1, 1, 0], [0.2, 0.2, 0.8, 0.8])          # ties
    yield ([0, 1], [1.0, 0.0])                          # extreme probabilities
    yield ([0, 1], [0.5, 0.5])                          # single distinct score
    yield ([0, 1, 0, 1], [-2.0, 5.0, 0.3, 3.0])         # scores outside [0, 1]
    yield ([0, 1], [1e9, -1e9])                         # large magnitudes
    yield ([0, 1], [1e308, -1e308])                     # near float extremes
    yield ([0, 1, 0], [0.0, -0.5, 5e-324])              # zero / subnormal
    yield ([0, 0, 0, 0, 1, 1], [0.0, 0.2, 0.5, 0.6, 0.7, 1.0])
    yield ([0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1],
           [0.0, 0.1, 0.6, 0.6, 0.7, 0.8, 0.9, 0.6, 0.7, 0.8, 0.9, 0.9, 1.0])
    yield ([1, 0], [-1.0, -2.0])                        # all-negative scores


def gen_case(rng):
    n = rng.randint(2, 20)
    # both classes present so the curve is non-degenerate
    y_true = [0, 1] + [rng.randint(0, 1) for _ in range(n - 2)]
    rng.shuffle(y_true)
    mode = rng.randrange(4)
    if mode == 0:        # probability estimates in [0, 1]
        y_score = [rng.random() for _ in range(n)]
    elif mode == 1:      # arbitrary confidences
        y_score = [rng.uniform(-10.0, 10.0) for _ in range(n)]
    elif mode == 2:      # large magnitudes
        y_score = [rng.uniform(-1e6, 1e6) for _ in range(n)]
    else:                # heavy ties: few distinct values
        vals = [rng.uniform(-5.0, 5.0) for _ in range(rng.randint(1, 4))]
        y_score = [rng.choice(vals) for _ in range(n)]
    return y_true, y_score


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    cases = list(boundary_cases())
    cases += [gen_case(rng) for _ in range(N_FUZZ)]

    for idx, (y_true, y_score) in enumerate(cases):
        yt = np.asarray(y_true)
        ys = np.asarray(y_score, dtype=np.float64)

        # --- primary leg: exact differential on the unpruned path --------
        # pre-anchoring input from the real unchanged upstream helper
        _, _, pre = _binary_clf_curve(yt, ys)
        model_in = as_model_list(pre)
        assert len(model_in) >= 1  # Requires of the modeled function
        count += 1
        shadow = anchor_thresholds(model_in)
        _, _, oracle_arr = roc_curve(yt, ys, drop_intermediate=False)
        oracle = as_model_list(oracle_arr)
        if not lists_equal(shadow, oracle):
            disagreements.append((y_true, y_score, "drop_intermediate=False",
                                  shadow, oracle))

        # --- second leg: the pruned path (sampled to bound runtime) ------
        if idx < 20_000:
            _, _, oracle_arr2 = roc_curve(yt, ys)  # default pruning on
            oracle2 = as_model_list(oracle_arr2)
            pre2 = oracle2[1:]  # the pruned pre-anchoring array, by structure
            if len(pre2) >= 1:
                count += 1
                shadow2 = anchor_thresholds(pre2)
                if not lists_equal(shadow2, oracle2):
                    disagreements.append((y_true, y_score,
                                          "drop_intermediate=True",
                                          shadow2, oracle2))

        if len(disagreements) >= 5:
            break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s) over %d inputs (seed=%d):"
              % (len(disagreements), count, SEED))
        for yt_, ys_, leg, sh, orc in disagreements:
            print("  y_true=%r y_score=%r leg=%s\n    shadow=%r\n    oracle=%r"
                  % (yt_, ys_, leg, sh, orc))
        return 1
    print("G-CONF OK: model.py impl shadow (List[float] carrier, real "
          "numpy.inf callee) agrees with the real patched roc_curve "
          "thresholds on %d inputs (seed=%d), 0 disagreements."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
