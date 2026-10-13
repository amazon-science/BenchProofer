#!/usr/bin/env python3
"""G-AX for pydata__xarray-7233 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference: the
behavior the patch changes — which names are re-promoted to coordinates of the
reshaped result (`should_be_coords`) — is modeled DEEPLY as a pure set
expression over the observable inputs (the reshaped-dimension names and the prior
coordinate names): a filter (the set intersection) followed by a union with the
prior coordinate names. SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled
changed op, so there is no callee contract to validate against the real repo. The
R legs are validated by G-CONF.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "pydata__xarray-7233",
    "reason": "no consumed callee axiom and no A-reference; impl is all R "
              "(validated by G-CONF)",
}))
sys.exit(0)
