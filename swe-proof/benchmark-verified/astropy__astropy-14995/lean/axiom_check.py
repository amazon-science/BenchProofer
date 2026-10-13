#!/usr/bin/env python3
"""G-AX for astropy__astropy-14995 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference: the
mask-propagation decision (`_arithmetic_mask`) is modeled DEEPLY over the
observable inputs (whether each operand carries a mask, whether a combining
function was supplied). The combining function `handle_mask` is an explicit
INPUT parameter of the modeled routine (the spec quantifies over all
`Combine = Mask -> Mask -> Mask`), not an axiomatized callee. SPEC_GUIDE §3
forbids axiomatizing a deeply-modeled changed decision, so there is no callee
contract to validate against the real repo. The R legs are validated by G-CONF.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "astropy__astropy-14995",
    "reason": "no consumed callee axiom and no A-reference; impl is all R "
              "(validated by G-CONF)",
}))
sys.exit(0)
