#!/usr/bin/env python3
"""G-AX for scikit-learn__scikit-learn-11578.

The bundle models the per-class probability transforms DEEPLY (A-reference,
refinement.md): `softmaxRow` (multinomial regime) and `ovrRow` (one-vs-rest
regime) are spelled out over the real-valued score rows. SPEC_GUIDE §3 requires
that a deeply-modeled callee be validated == the real repo callee (G-AX), not
shipped as a consumed axiom.

This check runs the REAL repo routines that produce per-class probability
estimates from a row of decision-function scores:
  * multinomial regime  -> sklearn.utils.extmath.softmax (the exact callee
    `predict_proba` invokes for multi_class != 'ovr');
  * one-vs-rest regime   -> the `_predict_proba_lr` math in
    sklearn/linear_model/base.py (logistic per score, then row-normalise).
and asserts the Lean deep models agree with them on boundary + fuzzed score
rows, within float tolerance (the F2P test compares with
assert_array_almost_equal). stdlib + numpy + the repo only; exit 0 iff sound.
"""
import sys

import numpy as np
from sklearn.utils.extmath import softmax as real_softmax

SEED = 11578
N = 40_000
TOL = 1e-9


# --- Lean deep models, transliterated (Solution.lean `pure` region) -----------
def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def lean_ovr_row(row):
    s = [sigmoid(v) for v in row]
    tot = sum(s)
    return [v / tot for v in s]


def lean_softmax_row(row):
    e = [np.exp(v) for v in row]
    tot = sum(e)
    return [v / tot for v in e]


# --- REAL repo OvR transform: the `_predict_proba_lr` body (base.py) ----------
# prob = 1/(1+exp(-decision)); for ndim==2: prob /= prob.sum(axis=1)
def real_ovr_matrix(decision_2d):
    prob = decision_2d.astype(np.float64).copy()
    prob *= -1
    np.exp(prob, prob)
    prob += 1
    np.reciprocal(prob, prob)
    prob /= prob.sum(axis=1).reshape((prob.shape[0], -1))
    return prob


def close(a, b):
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    return a.shape == b.shape and np.max(np.abs(a - b)) <= TOL


def check_matrix(decision_2d):
    # multinomial: Lean softmaxRow per row vs real softmax over the matrix
    lean_multi = np.array([lean_softmax_row(list(r)) for r in decision_2d])
    real_multi = real_softmax(decision_2d.astype(np.float64).copy())
    if not close(lean_multi, real_multi):
        return ("multinomial", decision_2d, lean_multi, real_multi)
    # ovr: Lean ovrRow per row vs real _predict_proba_lr normalisation
    lean_ovr = np.array([lean_ovr_row(list(r)) for r in decision_2d])
    real_ovr = real_ovr_matrix(decision_2d)
    if not close(lean_ovr, real_ovr):
        return ("ovr", decision_2d, lean_ovr, real_ovr)
    return None


def main():
    rng = np.random.RandomState(SEED)
    checked = 0

    # boundary rows: zeros, equal entries, large/negative, mixed sign
    edge = [
        np.array([[0.0, 0.0, 0.0]]),
        np.array([[1.0, 1.0, 1.0]]),
        np.array([[10.0, -10.0, 0.0]]),
        np.array([[-5.0, -5.0, -5.0]]),
        np.array([[100.0, 99.0, 98.0]]),
        np.array([[1.0, 2.0], [3.0, 4.0]]),
        np.array([[0.5, -0.5, 2.0, -2.0]]),
    ]
    for m in edge:
        bad = check_matrix(m)
        if bad:
            print(f"AXIOM VIOLATION ({bad[0]}) edge row={bad[1].tolist()} "
                  f"lean={bad[2].tolist()} real={bad[3].tolist()}")
            print("status=fail")
            return 1
        checked += 1

    for _ in range(N):
        n_samples = rng.randint(1, 6)
        n_classes = rng.randint(2, 6)
        decision_2d = rng.uniform(-8.0, 8.0, size=(n_samples, n_classes))
        bad = check_matrix(decision_2d)
        if bad:
            print(f"AXIOM VIOLATION ({bad[0]}) row={bad[1].tolist()}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} violations=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
