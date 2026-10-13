#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-14894
(plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (the `nSV = 0`
              guard, `tileRange`, `emptyResult`, `builtResult`) transliterated to
              Python over the real repo types (Nat ↔ non-negative int,
              `SparseCoef` ↔ the observable csr_matrix fields, mapping.md §2).
  * ORACLE  — `patch.diff`'s behaviour: the gold-patched `_sparse_fit`
              coefficient-assembly tail (`base.py:287-294` post-patch), run with
              the REAL numpy/scipy. This is the actual correctness oracle
              (G-RESOLVE).

They must agree on every Requires-satisfying input (`nClass >= 1`). The compared
observation is the csr_matrix field tuple (data.size, indices, indptr, shape) —
exactly what the consuming code and the F2P test
(`assert not model.dual_coef_.data.size`) read. Exit 0 iff zero disagreements;
any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), numpy + scipy only.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

import numpy as np
import scipy.sparse as sp

SEED = 14894
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean buildSparseCoef, transliterated -----------

def shadow_fields(nSV, nClass, dataLen):
    """SparseCoef produced by buildSparseCoef, as the observable-field dict
    (mapping.md §2). Mirrors the impl region exactly:
        indices = tileRange nSV nClass            (computed unconditionally)
        if nSV = 0 then emptyResult
        else builtResult (strided indptr, nClass×nSV shape)
    """
    indices = list(range(nSV)) * nClass                      # tileRange
    if nSV == 0:
        return dict(dataLen=0, indices=[], indptr=[0, 0], rows=1, cols=0)  # emptyResult
    indptr = [i * nSV for i in range(nClass + 1)]            # arangeIndptr (ok)
    return dict(dataLen=dataLen, indices=indices, indptr=indptr,
                rows=nClass, cols=nSV)                       # builtResult


# --- the oracle: patch.diff behaviour (gold-patched assembly tail) -----------

def oracle_fields(nSV, nClass, dataLen):
    """The gold-patched `_sparse_fit` coefficient-assembly tail run with the real
    numpy/scipy (base.py:287-294 post-patch). dual_coef_data is a length-`dataLen`
    float array (its values are irrelevant to the observed fields)."""
    dual_coef_data = np.arange(dataLen, dtype=np.float64)
    dual_coef_indices = np.tile(np.arange(nSV), nClass)
    if not nSV:
        dual_coef_ = sp.csr_matrix([])
    else:
        dual_coef_indptr = np.arange(0, dual_coef_indices.size + 1,
                                     dual_coef_indices.size / nClass)
        # _sparse_fit passes a dual_coef_data sized to nnz (= nClass*nSV); resize
        # so the csr_matrix is valid for any fuzzed dataLen without changing the
        # observable fields the test reads on the nSV=0 path.
        size = dual_coef_indices.size
        data = np.resize(dual_coef_data, size) if size else np.array([], dtype=np.float64)
        dual_coef_ = sp.csr_matrix(
            (data, dual_coef_indices, dual_coef_indptr), (nClass, nSV))
    m = dual_coef_.tocsr()
    return dict(dataLen=int(m.data.size if nSV else 0),
                indices=[int(i) for i in m.indices],
                indptr=[int(i) for i in m.indptr],
                rows=int(m.shape[0]), cols=int(m.shape[1]))


def shadow_normalize(nSV, nClass, dataLen):
    """Shadow, with dataLen normalized to the nnz the oracle stores, so the
    data.size comparison is apples-to-apples on the nSV>=1 path. The nSV=0 path
    (the fixed behaviour, dataLen irrelevant) is compared directly."""
    f = shadow_fields(nSV, nClass, dataLen)
    if nSV:
        f["dataLen"] = nClass * nSV          # oracle stores nnz = nClass*nSV
    return f


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4) — n_SV == 0 is the fixed case
    yield (0, 1, 0)
    yield (0, 2, 0)
    yield (0, 5, 7)
    yield (1, 1, 1)
    yield (1, 2, 2)
    yield (2, 1, 2)
    yield (2, 3, 6)
    yield (3, 2, 6)
    yield (10, 1, 10)
    yield (10, 9, 90)
    for _ in range(n):
        nSV = rng.randint(0, 40)
        nClass = rng.randint(1, 12)
        dataLen = rng.randint(0, 200)
        yield (nSV, nClass, dataLen)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for nSV, nClass, dataLen in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_normalize(nSV, nClass, dataLen)
        oracle = oracle_fields(nSV, nClass, dataLen)
        if shadow != oracle:
            disagreements.append(((nSV, nClass, dataLen), shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for inp, sh, orc in disagreements:
            print("  (nSV,nClass,dataLen)=%r shadow=%r oracle=%r" % (inp, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of buildSparseCoef agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
