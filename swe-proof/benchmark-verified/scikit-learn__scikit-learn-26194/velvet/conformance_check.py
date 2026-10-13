#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-26194.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region, transliterated
              to Python over the real repo types. The impl is the single prepend
              `Threshold.top :: finiteSeq base`:
                - `base` (the input carrier) is obtained by running the REAL
                  unchanged upstream pipeline `_binary_clf_curve` + the
                  `drop_intermediate` mask (mapping.md §1; NOT under test here);
                - `finiteSeq base` is the identity on content (the existing
                  thresholds, unchanged, in order);
                - `Threshold.top` ↔ `np.inf` (mapping.md §2).
              So the shadow's `thresholds` is `np.r_[np.inf, base]`.
              There are no A-tagged callees inside the impl region — the shadow
              is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the patched `roc_curve` applied at
              base_commit (the real correctness oracle, G-RESOLVE). The harness
              applies the gold patch before this runs.

They must agree on the returned `thresholds` for every Requires-satisfying input
(`base ≠ []`, i.e. a well-posed binary problem). The two other returns of
`roc_curve` (`fpr`, `tpr`) are untouched by the patch; we still assert they are
bit-identical between two oracle calls is unnecessary — we compare the SHADOW
thresholds to the ORACLE thresholds, the only value the change affects.

Exit 0 iff zero disagreements. Runs in-container, PYTHONPATH=/testbed so the
patched in-tree `sklearn` wins. Imports numpy + the repo. Fuzz seed pinned
(mapping.md §4) for a deterministic verdict.
"""
import random
import sys

import numpy as np

from sklearn.metrics import roc_curve                 # ORACLE: patched roc_curve
from sklearn.metrics._ranking import _binary_clf_curve  # input carrier (unchanged)

SEED = 26194
N_FUZZ = 100_000


def shadow_thresholds(y_true, y_score, drop_intermediate):
    """R/I shadow of withLeadingSentinel: prepend np.inf (Threshold.top) to the
    finite threshold carrier `base` produced by the real upstream pipeline."""
    fps, tps, thresholds = _binary_clf_curve(y_true, y_score)
    if drop_intermediate and len(fps) > 2:
        optimal_idxs = np.where(
            np.r_[True, np.logical_or(np.diff(fps, 2), np.diff(tps, 2)), True]
        )[0]
        thresholds = thresholds[optimal_idxs]
    base = thresholds
    if base.shape[0] == 0:               # Requires: base ≠ []
        return None
    # Threshold.top :: finiteSeq base
    return np.r_[np.inf, base]


def oracle_thresholds(y_true, y_score, drop_intermediate):
    """patch.diff's behaviour: the patched roc_curve's returned thresholds."""
    _, _, thresholds = roc_curve(
        y_true, y_score, drop_intermediate=drop_intermediate)
    return thresholds


def agree(a, b):
    """Compare two threshold vectors elementwise: same length, np.inf matched
    exactly as inf, finite parts equal up to float tolerance."""
    if a is None:
        return True  # Requires not satisfied -> out of scope
    if a.shape != b.shape:
        return False
    a_inf, b_inf = np.isinf(a), np.isinf(b)
    if not np.array_equal(a_inf, b_inf):
        return False
    # signs of the infinities must match too
    if not np.array_equal(np.sign(a[a_inf]), np.sign(b[b_inf])):
        return False
    return np.allclose(a[~a_inf], b[~b_inf], rtol=1e-12, atol=0.0)


def fuzz_inputs(n, rng, nprng):
    # boundary cases first
    yield (np.random.RandomState(42).randint(0, 2, size=10),
           np.random.RandomState(42).rand(10), True)
    yield ([0, 0, 0, 0, 1, 1], [0.0, 0.2, 0.5, 0.6, 0.7, 1.0], True)
    yield ([0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1],
           [0.0, 0.1, 0.6, 0.6, 0.7, 0.8, 0.9, 0.6, 0.7, 0.8, 0.9, 0.9, 1.0], True)
    yield ([1, 1, 2, 2], [0.1, 0.4, 0.35, 0.8], True)   # docstring (pos_label default fails -> skip below)
    yield ([0, 1], [0.2, 0.8], True)
    yield ([0, 1], [0.2, 0.8], False)
    yield ([0, 0, 1, 1], [0.0, 1.0, 0.0, 1.0], True)
    yield ([0, 1, 0, 1], [10.0, 200.0, -5.0, 3.0], True)
    for _ in range(n):
        k = rng.randint(2, 40)
        y_true = nprng.randint(0, 2, size=k)
        if y_true.min() == y_true.max():
            y_true[0] = 1 - y_true[0]
        kind = rng.randint(0, 2)
        if kind == 0:
            y_score = nprng.rand(k)
        elif kind == 1:
            y_score = nprng.rand(k) * 1000 - 500
        else:
            y_score = nprng.randint(0, 4, size=k).astype(float) / 4.0
        drop = bool(rng.randint(0, 1))
        yield (y_true, y_score, drop)


def main():
    rng = random.Random(SEED)
    nprng = np.random.RandomState(SEED)
    disagreements = []
    count = 0
    for y_true, y_score, drop in fuzz_inputs(N_FUZZ, rng, nprng):
        y_true = np.asarray(y_true)
        y_score = np.asarray(y_score, dtype=float)
        # roc_curve needs {0,1} or {-1,1} labels with default pos_label; skip
        # the multi-label docstring fixture (pos_label!=None there).
        uniq = set(np.unique(y_true).tolist())
        if not (uniq <= {0, 1} or uniq <= {-1, 1}):
            continue
        count += 1
        try:
            shadow = shadow_thresholds(y_true, y_score, drop)
            oracle = oracle_thresholds(y_true, y_score, drop)
        except Exception as e:  # pragma: no cover
            disagreements.append((y_true.tolist(), y_score.tolist(), "exc:%r" % e, None))
            if len(disagreements) >= 5:
                break
            continue
        if not agree(shadow, oracle):
            disagreements.append((y_true.tolist(), y_score.tolist(),
                                  None if shadow is None else shadow.tolist(),
                                  oracle.tolist()))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for yt, ys, sh, orc in disagreements:
            print("  y_true=%r y_score=%r shadow=%r oracle=%r" % (yt, ys, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of withLeadingSentinel ([inf, *base]) agrees "
          "with patched roc_curve thresholds on %d inputs (seed=%d), 0 "
          "disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
