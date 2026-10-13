#!/usr/bin/env python3
"""G-AX for sympy__sympy-20801 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference: the
float equality dispatch (`floatEqResult`) is modeled DEEPLY over the observable
kind-flags of the operand together with the boolean outcomes of the unchanged
delegated comparisons (a named constant's own equality, a rational's own
equality, the shared-precision numeric comparison) and the zero/falsy probes,
all of which enter as plain data. SPEC_GUIDE §3 forbids axiomatizing a
deeply-modeled changed decision, so there is no callee contract to validate
against the real repo. The R legs are validated by G-CONF.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "sympy__sympy-20801",
    "reason": "no consumed callee axiom and no A-reference; impl is all R "
              "(validated by G-CONF)",
}))
sys.exit(0)
