#!/usr/bin/env python3
"""G-AX executable soundness check for scikit-learn__scikit-learn-26194.

This bundle declares NO Lean axioms and NO deep-model references: the changed
operation (prepending one leading threshold) is modeled directly. What G-AX must
still discharge are the two STRUCTURAL facts the spec's typing + `require` rely on
about the input carrier `base` — the finite-threshold vector that the anchoring
step receives. `base` is produced by the UNCHANGED upstream callee
`_binary_clf_curve` followed by the unchanged `drop_intermediate` mask. We run
those REAL repo functions over boundary + fuzzed inputs and assert:

  1. `base` is NON-EMPTY            -> justifies `require base ≠ []`
  2. every element of `base` is FINITE -> justifies the `Rat`/`Threshold.value`
       carrier, and the claim that the new `np.inf` lead is categorically above
       every finite score (Threshold.top ≠ any value).

These are exactly the obligations mapping.md §3 cites. No value is pinned to a
model; we only observe that the real callee meets the structural contract the
spec assumes. Exit 0 iff both hold on every probed input.

Runs in-container (the prebuilt SWE-Bench instance image) with PYTHONPATH=/testbed
so the in-tree `sklearn` wins. Imports only numpy + the repo. The gold patch is
NOT required to be applied for this check (the callee is unchanged by it).
"""
import random
import sys

import numpy as np

# The real, unchanged upstream callee + the drop mask, exactly as roc_curve uses
# them at base_commit (sklearn/metrics/_ranking.py:1070-1083).
from sklearn.metrics._ranking import _binary_clf_curve


def base_thresholds(y_true, y_score, drop_intermediate, pos_label=None):
    """Reproduce, with the REAL callee, the `thresholds` vector that the
    anchoring step (line 1086) receives — i.e. `base` in Solution.lean.

    `pos_label` is threaded through exactly as `roc_curve` does
    (`_binary_clf_curve(..., pos_label=pos_label, ...)`, _ranking.py:1061): it is
    REQUIRED whenever `y_true` is not in {0,1}/{-1,1} (the callee raises a
    ValueError otherwise via `_check_pos_label_consistency`)."""
    fps, tps, thresholds = _binary_clf_curve(y_true, y_score, pos_label=pos_label)
    # the exact drop_intermediate mask from roc_curve (_ranking.py:1075-1083)
    if drop_intermediate and len(fps) > 2:
        optimal_idxs = np.where(
            np.r_[True, np.logical_or(np.diff(fps, 2), np.diff(tps, 2)), True]
        )[0]
        thresholds = thresholds[optimal_idxs]
    return thresholds


def check(y_true, y_score, drop_intermediate, label, pos_label=None):
    base = base_thresholds(y_true, y_score, drop_intermediate, pos_label=pos_label)
    assert base.shape[0] >= 1, (
        "structural fact 1 (non-empty base) VIOLATED on %s: base=%r"
        % (label, base))
    assert np.all(np.isfinite(base)), (
        "structural fact 2 (all-finite base) VIOLATED on %s: base=%r"
        % (label, base))


def main():
    rng = random.Random(26194)
    nprng = np.random.RandomState(26194)

    checked = 0

    # --- boundary cases ------------------------------------------------------
    # Each tuple is (y_true, y_score, drop_intermediate, pos_label). `pos_label`
    # is REQUIRED whenever y_true is not {0,1}/{-1,1}, exactly as roc_curve
    # requires it (the real callee raises otherwise); None means "binary, use
    # the default" — matching how the F2P tests call roc_curve.
    boundary = [
        # the problem-statement probability-estimate case (the F2P)
        (np.random.RandomState(42).randint(0, 2, size=10),
         np.random.RandomState(42).rand(10), True, None),
        # the test_roc_curve_drop_intermediate fixtures
        ([0, 0, 0, 0, 1, 1], [0.0, 0.2, 0.5, 0.6, 0.7, 1.0], True, None),
        ([0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1],
         [0.0, 0.1, 0.6, 0.6, 0.7, 0.8, 0.9, 0.6, 0.7, 0.8, 0.9, 0.9, 1.0], True, None),
        # docstring example — labels {1,2}, so pos_label=2 (as the docstring calls it)
        ([1, 1, 2, 2], [0.1, 0.4, 0.35, 0.8], True, 2),
        # minimal / degenerate shapes
        ([0, 1], [0.2, 0.8], True, None),
        ([0, 1], [0.2, 0.8], False, None),
        ([0, 1], [0.5, 0.5], True, None),       # tied scores
        ([1, 1], [0.3, 0.7], True, None),       # no negative class
        ([0, 0], [0.3, 0.7], True, None),       # no positive class
        # scores well above 1 (confidence values, not probabilities)
        ([0, 1, 0, 1], [10.0, 200.0, -5.0, 3.0], True, None),
        # scores at exactly 1.0 / 0.0 (the boundary the issue is about)
        ([0, 0, 1, 1], [0.0, 1.0, 0.0, 1.0], True, None),
        # non-{0,1} binary labels passed with an explicit pos_label (-1/1 and str)
        ([-1, -1, 1, 1], [0.1, 0.4, 0.35, 0.8], True, None),
        (["neg", "pos", "neg", "pos"], [0.2, 0.9, 0.4, 0.7], True, "pos"),
    ]
    for y_true, y_score, drop, pos_label in boundary:
        check(np.asarray(y_true), np.asarray(y_score, dtype=float), drop,
              "boundary %r" % (list(np.ravel(y_score))[:6],), pos_label=pos_label)
        checked += 1

    # --- randomized fuzz -----------------------------------------------------
    for _ in range(20000):
        n = rng.randint(2, 40)
        # ensure at least one of each class so _binary_clf_curve is well-posed
        y_true = nprng.randint(0, 2, size=n)
        if y_true.min() == y_true.max():
            y_true[0] = 1 - y_true[0]
        kind = rng.randint(0, 2)
        if kind == 0:
            y_score = nprng.rand(n)                 # probability estimates [0,1)
        elif kind == 1:
            y_score = nprng.rand(n) * 1000 - 500    # arbitrary confidence values
        else:
            # many ties (stresses distinct-value / drop logic)
            y_score = nprng.randint(0, 4, size=n).astype(float) / 4.0
        drop = bool(rng.randint(0, 1))
        check(y_true, y_score, drop, "fuzz n=%d kind=%d" % (n, kind))
        checked += 1

    print("G-AX OK: real _binary_clf_curve(+drop) yields a non-empty, all-finite "
          "threshold carrier `base` on %d inputs (seed=26194) — `require base ≠ []` "
          "and the finite-`Rat` carrier are sound." % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
