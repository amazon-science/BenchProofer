#!/usr/bin/env python3
"""G-AX for scikit-learn__scikit-learn-26323 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference: the
behavior the patch changes — propagating the chosen output container to the
fall-back `remainder` transformer in `ColumnTransformer.set_output` — is modeled
DEEPLY (the pure helper `setOutput`: an estimator records the new container, a
reserved `"passthrough"`/`"drop"` sentinel is left unchanged). The contained
transformer collection and the remainder slot enter as plain grounded input data.
SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled changed op, so there is no
callee contract to validate against the real repo. The R/I legs are validated by
G-CONF.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "scikit-learn__scikit-learn-26323",
    "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
              "(validated by G-CONF)",
}))
sys.exit(0)
