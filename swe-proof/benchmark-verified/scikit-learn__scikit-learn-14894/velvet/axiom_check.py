#!/usr/bin/env python3
"""G-AX executable soundness check for scikit-learn__scikit-learn-14894.

Executes the REAL library callees the modeled code region calls
(`numpy.arange`, `numpy.tile`, `scipy.sparse.csr_matrix`) — all UNCHANGED by the
gold patch — on boundary cases (including the degenerate no-rows case) plus
randomized fuzzing, and asserts that every observation matches the deep models
declared in Solution.lean's `axioms`/`pure` regions.

The kind-A checks (all A-reference — deep models, no consumed axioms):

  * `tileRange(nSV, nClass)`   == np.tile(np.arange(nSV), nClass).tolist()
  * `arangeIndptr(nSV, nClass)`:
        nSV == 0 : np.arange(0, size+1, size/nClass) RAISES ZeroDivisionError
                   (size/nClass == 0)            -> Except.error zeroDivision
        nSV >= 1 : == [0, nSV, 2*nSV, ..., nClass*nSV]   (Except.ok)
  * `emptyResult`   == observed fields of sp.csr_matrix([])
  * `builtResult`   == observed fields of the strided csr_matrix the else-branch
                       constructs.

Imports only `numpy` / `scipy.sparse` — the same libraries the gold patch calls.
Exit 0 iff every obligation holds.
"""
import random
import sys

import numpy as np
import scipy.sparse as sp


# --- Solution.lean deep-model reference encodings (in lock-step) -------------

def tile_range(nSV, nClass):
    """Solution.lean `tileRange`: column indices 0..nSV-1 tiled nClass times."""
    return list(range(nSV)) * nClass


def arange_indptr(nSV, nClass):
    """Solution.lean `arangeIndptr`. Returns ('error',) for the zeroDivision
    shape, or ('ok', list) for the strided pointer sequence."""
    if nSV == 0:
        return ("error",)
    return ("ok", [i * nSV for i in range(nClass + 1)])


# Solution.lean `emptyResult` field encoding.
EMPTY_RESULT = dict(dataLen=0, indices=[], indptr=[0, 0], rows=1, cols=0)


# --- the checks --------------------------------------------------------------

def check_tile_reference(nSV, nClass):
    observed = np.tile(np.arange(nSV), nClass).tolist()
    expected = tile_range(nSV, nClass)
    assert observed == expected, (
        "tileRange deep model unsound on (nSV=%d, nClass=%d): np.tile gave %r, "
        "deep model gives %r" % (nSV, nClass, observed, expected))


def check_arange_reference(nSV, nClass):
    """Run the REAL np.arange exactly as base.py:290-291 does and compare to the
    deep model arangeIndptr — including that nSV==0 raises ZeroDivisionError."""
    dual_coef_indices = np.tile(np.arange(nSV), nClass)
    size = dual_coef_indices.size
    model = arange_indptr(nSV, nClass)
    if model[0] == "error":
        # the deep model claims the strided arithmetic is ill-defined; the real
        # callee must indeed raise ZeroDivisionError (float division by zero).
        raised = False
        try:
            np.arange(0, size + 1, size / nClass)
        except ZeroDivisionError:
            raised = True
        assert raised, (
            "arangeIndptr claims zeroDivision at (nSV=%d, nClass=%d) but the "
            "real np.arange did not raise" % (nSV, nClass))
        return
    observed = [int(round(x)) for x in np.arange(0, size + 1, size / nClass).tolist()]
    expected = model[1]
    assert observed == expected, (
        "arangeIndptr deep model unsound on (nSV=%d, nClass=%d): np.arange gave "
        "%r, deep model gives %r" % (nSV, nClass, observed, expected))


def fields_of(m):
    """Observable SparseCoef fields of a real csr_matrix (mapping.md §2)."""
    m = m.tocsr()
    return dict(dataLen=int(m.data.size), indices=[int(i) for i in m.indices],
                indptr=[int(i) for i in m.indptr],
                rows=int(m.shape[0]), cols=int(m.shape[1]))


def check_empty_reference():
    observed = fields_of(sp.csr_matrix([]))
    assert observed == EMPTY_RESULT, (
        "emptyResult deep model unsound: sp.csr_matrix([]) observable fields are "
        "%r, deep model gives %r" % (observed, EMPTY_RESULT))
    # the property the F2P test actually observes:
    assert not sp.csr_matrix([]).data.size, "empty result must have no data"


def check_built_reference(nSV, nClass, dataLen):
    """For nSV>=1, build the strided csr_matrix exactly as base.py:289-294 and
    confirm its observable fields equal Solution.lean's `builtResult`."""
    dual_coef_indices = np.tile(np.arange(nSV), nClass)
    size = dual_coef_indices.size
    indptr = np.arange(0, size + 1, size / nClass)
    data = np.arange(dataLen, dtype=np.float64)
    # data length must match nnz implied by indptr (= nClass*nSV) for a valid
    # csr_matrix; the real _sparse_fit passes dual_coef_data of that size.
    data = np.resize(data, size) if size else np.array([], dtype=np.float64)
    m = sp.csr_matrix((data, dual_coef_indices, indptr), (nClass, nSV))
    f = fields_of(m)
    assert f["indices"] == tile_range(nSV, nClass), (
        "builtResult indices mismatch on (nSV=%d,nClass=%d): %r" % (nSV, nClass, f["indices"]))
    assert f["indptr"] == arange_indptr(nSV, nClass)[1], (
        "builtResult indptr mismatch on (nSV=%d,nClass=%d): %r" % (nSV, nClass, f["indptr"]))
    assert (f["rows"], f["cols"]) == (nClass, nSV), (
        "builtResult shape mismatch on (nSV=%d,nClass=%d): %r" % (nSV, nClass, (f["rows"], f["cols"])))


def main():
    # --- boundary (nSV, nClass) pairs -- include the degenerate no-rows case --
    boundary = [(0, 1), (0, 2), (0, 5),          # n_SV == 0 : the fixed case
                (1, 1), (1, 2), (1, 5),
                (2, 1), (2, 3), (3, 2),
                (4, 4), (7, 3), (10, 1), (10, 9)]
    for nSV, nClass in boundary:
        check_tile_reference(nSV, nClass)
        check_arange_reference(nSV, nClass)
        if nSV >= 1:
            check_built_reference(nSV, nClass, dataLen=nSV * nClass)

    check_empty_reference()

    # --- randomized fuzz ------------------------------------------------------
    rng = random.Random(14894)
    n_fuzz = 20000
    for _ in range(n_fuzz):
        nSV = rng.randint(0, 40)
        nClass = rng.randint(1, 12)
        check_tile_reference(nSV, nClass)
        check_arange_reference(nSV, nClass)
        if nSV >= 1:
            check_built_reference(nSV, nClass, dataLen=nSV * nClass)

    print("G-AX OK: tileRange / arangeIndptr / emptyResult / builtResult deep "
          "models sound vs real numpy.arange/tile + scipy.csr_matrix on %d "
          "boundary + %d fuzz (nSV,nClass) pairs (incl. nSV=0 zeroDivision)."
          % (len(boundary), n_fuzz))
    return 0


if __name__ == "__main__":
    sys.exit(main())
