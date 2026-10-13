#!/usr/bin/env python3
"""G-AX for scikit-learn__scikit-learn-13779 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference: the
behavior the patch changes — passing over a `None`/empty estimator slot in the
`sample_weight`-support validation loop of `_BaseVoting.fit` — is modeled DEEPLY
(the `none` branch of the loop's `match`, vs. the pre-patch impl that rejects on a
`None` slot). The unchanged callee `has_fit_parameter(step, 'sample_weight')`
returns a plain boolean that enters as grounded input data (the `some accepts`
flag per present slot); it is never axiomatized. SPEC_GUIDE §3 forbids
axiomatizing a deeply-modeled changed op, so there is no callee contract to
validate against the real repo. The R/I legs are validated by G-CONF.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "scikit-learn__scikit-learn-13779",
    "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
              "(validated by G-CONF)",
}))
sys.exit(0)
