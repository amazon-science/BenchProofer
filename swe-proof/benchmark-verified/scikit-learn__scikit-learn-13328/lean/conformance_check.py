#!/usr/bin/env python3
"""G-CONF for scikit-learn__scikit-learn-13328 — skip stub.

The impl region's substantive operation is the deep model of the UNCHANGED
input-validation callee (`check_X_y`/`check_array` element-type resolution under
`dtype=[np.float64, np.float32]`) — an A-reference. There is no independent R/I
arithmetic leg in the impl to differential-test: the whole behavior IS the callee
model, and that model is validated against the real repo routine by `axiom_check.py`
(G-AX). Per SPEC_GUIDE §3 / the worker spec, when the impl region is all-A-tagged
G-CONF is skipped (`meta.json conf_skip=true`).
"""
import json
import sys

if __name__ == "__main__":
    print(json.dumps({
        "status": "skip",
        "instance": "scikit-learn__scikit-learn-13328",
        "reason": "impl region is the A-reference deep model of the unchanged "
                  "check_array dtype resolution (validated by G-AX); no "
                  "independent R/I leg to differential-test",
    }))
    sys.exit(0)
