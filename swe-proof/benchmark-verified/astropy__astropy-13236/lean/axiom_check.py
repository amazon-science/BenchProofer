#!/usr/bin/env python3
"""G-AX for astropy__astropy-13236 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference: the
column-class decision (`convResultClass`) is modeled DEEPLY over the observable
flags of the input (already-a-column, already-a-mixin, first-element-is-a-mixin,
masked, null, has-a-dtype, structured field count) together with the classes the
unchanged upstream sub-decisions yield, which enter as plain data. SPEC_GUIDE §3
forbids axiomatizing a deeply-modeled changed decision, so there is no callee
contract to validate against the real repo. The R legs are validated by G-CONF.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "astropy__astropy-13236",
    "reason": "no consumed callee axiom and no A-reference; impl is all R "
              "(validated by G-CONF)",
}))
sys.exit(0)
