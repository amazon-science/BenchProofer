#!/usr/bin/env python3
"""G-AX for scikit-learn__scikit-learn-14894 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference. The
operations the patch guards — repeating the support ramp (`np.tile∘np.arange`),
building the evenly spaced row offsets (`np.arange`), the empty-matrix sentinel
(`sp.csr_matrix([])`), and assembling the CSR triple — are modeled DIRECTLY
(deep model) as `tileRange` / `rowOffsets` / `emptyCSR` / record fields
(refinement.md rows are all I/R). SPEC_GUIDE §3 forbids axiomatizing a
deeply-modeled changed op, so there is no callee contract to validate against
the real repo. The deep models are differential-tested by G-CONF.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "scikit-learn__scikit-learn-14894",
    "reason": "no consumed callee axiom and no A-reference; impl is all I/R "
              "(deep model of tile/arange/csr_matrix), validated by G-CONF",
}))
sys.exit(0)
