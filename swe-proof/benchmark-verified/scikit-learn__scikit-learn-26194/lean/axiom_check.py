#!/usr/bin/env python3
"""G-AX for scikit-learn__scikit-learn-26194 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference: the
behavior the patch changes — the value placed at the leading threshold position in
`roc_curve` — is modeled DEEPLY (a distinct `Thr.posInf` constructor for the
`np.inf` sentinel, vs. the arithmetic `Thr.finite (max+1)` it replaced). The
decreasing finite score thresholds produced upstream enter as plain grounded input
data (`ts`). SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled changed op, so
there is no callee contract to validate against the real repo. The R/I legs are
validated by G-CONF.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "scikit-learn__scikit-learn-26194",
    "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
              "(validated by G-CONF)",
}))
sys.exit(0)
