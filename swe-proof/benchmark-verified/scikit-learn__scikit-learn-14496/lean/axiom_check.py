#!/usr/bin/env python3
"""G-AX for scikit-learn__scikit-learn-14496 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference. The
modeled behavior (`resolveMinSamples`, `resolveThresholds`) is the threshold
normalization itself, modeled deeply (all R/I, validated by G-CONF). The only
callee in the changed region, the threshold-range validator (`_validate_size`),
merely rejects out-of-range inputs and does not transform the value; its guarantee
is carried as the `0 < ·` precondition on `correct_*`, not as a consumed contract.
There is therefore no callee axiom to validate against the real repo.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "scikit-learn__scikit-learn-14496",
    "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
              "(validated by G-CONF)",
}))
sys.exit(0)
