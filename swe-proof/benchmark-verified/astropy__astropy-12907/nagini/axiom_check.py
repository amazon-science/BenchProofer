#!/usr/bin/env python3
"""G-AX executable fidelity check for astropy__astropy-12907.

There are NO consumed `@ContractOnly` axioms in this bundle: the behaviour
under specification — the side-by-side combination of two dependency matrices
that the `'&'` operator performs — is modelled DEEPLY in model.py (the pure
`expected_row` / `zeros` plus the verified row-building loop in
`parallel_dependency_matrix`). What this script validates is that the deep
model's row layout equals the array layout the gold patch produces.

The real (post-fix) operation, `astropy/modeling/separable.py::_cstack`, in the
ndarray x ndarray branch the patch touches, is:

    noutp = left.shape[0] + right.shape[0]
    cleft = np.zeros((noutp, left.shape[1]))
    cleft[: left.shape[0], : left.shape[1]] = left
    cright = np.zeros((noutp, right.shape[1]))
    cright[-right.shape[0]:, -right.shape[1]:] = right   # the FIX (was = 1)
    return np.hstack([cleft, cright])

i.e. the stacked matrix is block-diagonal: `left` in the upper-left block,
`right` (its ACTUAL entries) in the lower-right block, zeros elsewhere. That is
exactly what model.py's `expected_row` encodes:
  row i<lr  ==  left[i]  ++  zeros(rc)
  row i>=lr ==  zeros(lc) ++ right[i-lr]

`reference_cstack` below is a faithful, dependency-free numpy reimplementation
of that real branch. `model_expected_row` mirrors model.py's deep model. We
assert they agree on boundary cases + randomized fuzz over arbitrary 0/1
matrices (the separability matrices the operator stacks). If `astropy` is
importable we ADDITIONALLY drive the real `separability_matrix` on the two
nested compound models the F2P tests add and confirm the model reproduces them.

Exit 0 iff every observation matches the model.
"""
import random
import sys

import numpy as np


# --- the real (post-fix) _cstack ndarray x ndarray branch, reimplemented -----

def reference_cstack(left, right):
    """Faithful numpy reimplementation of the gold _cstack branch (both
    operands already coord matrices)."""
    left = np.asarray(left, dtype=float)
    right = np.asarray(right, dtype=float)
    noutp = left.shape[0] + right.shape[0]
    cleft = np.zeros((noutp, left.shape[1]))
    cleft[: left.shape[0], : left.shape[1]] = left
    cright = np.zeros((noutp, right.shape[1]))
    cright[-right.shape[0]:, -right.shape[1]:] = right     # the fix
    return np.hstack([cleft, cright])


# --- model.py's deep model, reimplemented as row layout ----------------------

def model_expected_row(left, right, lr, lc, rr, rc, i):
    if i < lr:
        return list(left[i]) + [0] * rc
    return [0] * lc + list(right[i - lr])


def model_matrix(left, right):
    left = [list(r) for r in left]
    right = [list(r) for r in right]
    lr = len(left); lc = len(left[0]) if lr else 0
    rr = len(right); rc = len(right[0]) if rr else 0
    return [model_expected_row(left, right, lr, lc, rr, rc, i)
            for i in range(lr + rr)]


def check_pair(left, right):
    real = reference_cstack(left, right)
    model = np.array(model_matrix(left, right), dtype=float)
    assert real.shape == model.shape, (
        "shape mismatch on left=%r right=%r: real %r model %r"
        % (left, right, real.shape, model.shape))
    assert np.array_equal(real, model), (
        "block-placement model unsound on left=%r right=%r:\nreal=\n%r\n"
        "model=\n%r" % (left, right, real, model))


def rand_matrix(rng, rmax=4, cmax=4):
    r = rng.randint(1, rmax)
    c = rng.randint(1, cmax)
    return [[rng.randint(0, 1) for _ in range(c)] for _ in range(r)]


# --- the real separability_matrix on the F2P nested models (best-effort) -----

def check_real_separability():
    """If astropy is importable, drive the real (patched) separability_matrix
    on the two nested compound models the F2P tests add and confirm the model
    reproduces the published expected matrices."""
    try:
        from astropy.modeling import models
        from astropy.modeling.separable import separability_matrix
    except Exception as exc:                       # deps absent on this host
        print("G-AX note: astropy not importable here (%s); relying on the "
              "numpy reimplementation of the patched _cstack branch." % exc)
        return 0

    rot = models.Rotation2D(2)
    sh1 = models.Shift(1); sh2 = models.Shift(2)
    scl1 = models.Scale(1); scl2 = models.Scale(2)

    cm_4d_expected = np.array([[True,  True,  False, False],
                               [True,  True,  False, False],
                               [False, False, True,  False],
                               [False, False, False, True]])
    cm11_expected = np.array([[True,  True,  False, False, False],
                              [True,  True,  False, False, False],
                              [False, False, True,  False, False],
                              [False, False, False, True,  False],
                              [False, False, False, False, True]])
    cases = [
        (rot & (sh1 & sh2), cm_4d_expected),                 # cm8 (F2P 6)
        (rot & sh1 & sh2, cm_4d_expected),                   # cm9
        ((rot & sh1) & sh2, cm_4d_expected),                 # cm10
        (rot & sh1 & (scl1 & scl2), cm11_expected),          # cm11 (F2P 9)
    ]
    for model, expected in cases:
        got = separability_matrix(model)
        assert np.array_equal(got, expected), (
            "real separability_matrix disagrees with the F2P expectation:\n"
            "got=\n%r\nexpected=\n%r" % (got, expected))
    print("G-AX: real separability_matrix matches all %d nested-model F2P "
          "expectations." % len(cases))
    return len(cases)


def main():
    # boundary cases: identity (independent) and all-ones (dependent) blocks,
    # 1x1, rectangular, and the actual nested-model coord matrices.
    eye2 = [[1, 0], [0, 1]]
    eye3 = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    ones2 = [[1, 1], [1, 1]]
    rot2 = [[1, 1], [1, 1]]                       # Rotation2D coord matrix
    boundary_pairs = [
        ([[1]], [[1]]),
        ([[1]], [[0]]),
        ([[0]], [[1]]),
        (eye2, eye2),
        (eye2, ones2),
        (rot2, eye2),                             # rot & (sh1 & sh2): cm8
        (rot2, [[1, 0, 0], [0, 1, 0], [0, 0, 1]]),
        (eye2, eye3),
        ([[1, 1], [0, 0]], [[1, 0], [0, 1]]),
        ([[1, 0]], [[0, 1], [1, 0]]),
        (eye3, [[1]]),
    ]
    for left, right in boundary_pairs:
        check_pair(left, right)

    rng = random.Random(12907)
    for _ in range(20000):
        check_pair(rand_matrix(rng), rand_matrix(rng))

    n_real = check_real_separability()

    print("G-AX OK: block-placement deep model == real _cstack layout on %d "
          "boundary + 20000 fuzz matrix pairs%s." % (
              len(boundary_pairs),
              " and %d real F2P models" % n_real if n_real else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
