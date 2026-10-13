#!/usr/bin/env python3
"""G-CONF for scikit-learn__scikit-learn-14894.

The gold patch is already applied to /testbed when this runs, so the
`dual_coef_` construction tail of `BaseLibSVM._sparse_fit` short-circuits the
empty-support case to `sp.csr_matrix([])`. We compare the R/I Python shadow of
`implementation_dualCoef` (the Lean impl, transliterated op-for-op per
refinement.md) against the REAL post-patch construction, reproduced verbatim
from sklearn/svm/base.py:283-297, reading back `.data / .indices / .indptr /
.shape`. Over >=1e5 fuzzed (n_SV, n_class) configurations — including the
n_SV = 0 boundary — zero disagreements => exit 0.

Type bijection (mapping.md):
  width  = n_SV     : int >= 0  <->  Nat
  rows   = n_class  : int >= 1  <->  Nat  (len(classes_)-1 or 1)
  data   = dual_coef_data       <->  List alpha (stored by identity)
  success / ZeroDivisionError   <->  Except.ok / Except.error
  CSR (.data,.indices,.indptr,.shape) <-> CSRMatrix(data,indices,indptr,nrows,ncols)

stdlib + numpy + scipy only.
"""
import random
import sys

import numpy as np
import scipy.sparse as sp

SEED = 14894
N = 120_000  # >= 10^5


def shadow(width, rows, data):
    """R/I shadow of implementation_dualCoef (refinement.md).

    Returns a normalized CSR tuple (data, indices, indptr, shape) on success, or
    the sentinel 'ERROR' if the modeled construction would abort. The shadow
    NEVER aborts (it mirrors the post-patch control flow), so it always returns
    a tuple."""
    indices = list(np.tile(np.arange(width), rows))  # tileRange width rows
    if width == 0:
        # emptyCSR: sp.csr_matrix([]) canonical attributes
        return ([], [], [0, 0], (1, 0))
    indptr = [i * width for i in range(rows + 1)]     # rowOffsets rows width
    return (list(data), indices, indptr, (rows, width))


def oracle(width, rows, data):
    """Real POST-PATCH construction, verbatim from sklearn/svm/base.py.

    n_SV = width, n_class = rows, dual_coef_data = data."""
    n_SV = width
    n_class = rows
    dual_coef_data = np.asarray(data, dtype=np.float64)
    dual_coef_indices = np.tile(np.arange(n_SV), n_class)
    if not n_SV:
        m = sp.csr_matrix([])
    else:
        dual_coef_indptr = np.arange(0, dual_coef_indices.size + 1,
                                     dual_coef_indices.size / n_class)
        m = sp.csr_matrix(
            (dual_coef_data, dual_coef_indices, dual_coef_indptr),
            (n_class, n_SV))
    return (list(m.data.astype(float)),
            list(int(i) for i in m.indices),
            list(int(i) for i in m.indptr),
            tuple(int(s) for s in m.shape))


def norm(t):
    data, indices, indptr, shape = t
    return ([round(float(x), 9) for x in data],
            [int(i) for i in indices],
            [int(i) for i in indptr],
            tuple(int(s) for s in shape))


def main():
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    # Deterministic boundary cases: the empty-support scenario (the F2P bug),
    # plus the smallest non-empty regression/classification shapes.
    fixed = [
        (0, 1, []),            # n_SV=0, regression (SVR) — the reported crash
        (0, 3, []),            # n_SV=0, multiclass (n_class=3)
        (1, 1, [0.5]),         # single support vector, regression
        (3, 1, [0.04, 0.10, 0.16]),
        (4, 2, [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]),
    ]
    cases = list(fixed)
    for _ in range(N):
        width = rng.randint(0, 60)
        rows = rng.randint(1, 6)
        data = [rng.uniform(-10.0, 10.0) for _ in range(width * rows)]
        cases.append((width, rows, data))

    for width, rows, data in cases:
        got = norm(shadow(width, rows, data))
        want = norm(oracle(width, rows, data))
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append(((width, rows, len(data)), got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for inp, g, w in examples:
            print(f"  in(width,rows,len)={inp}\n    shadow={g}\n    real  ={w}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
