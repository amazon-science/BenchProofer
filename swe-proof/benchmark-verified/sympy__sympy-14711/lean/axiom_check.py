#!/usr/bin/env python3
"""G-AX for sympy__sympy-14711 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference: the
addition behavior (operand classification — another vector / the additive
identity / anything else — and the resulting component list) is modeled DEEPLY
over the observable shape of the operand (`AddOperand`), with `_check_vector`'s
accept/raise effect folded into that classification. SPEC_GUIDE §3 forbids
axiomatizing a deeply-modeled changed decision, so there is no callee contract
to validate against the real repo. The R legs are validated by G-CONF.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "sympy__sympy-14711",
    "reason": "no consumed callee axiom and no A-reference; impl is all R "
              "(validated by G-CONF)",
}))
sys.exit(0)
