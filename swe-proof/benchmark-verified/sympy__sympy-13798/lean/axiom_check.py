#!/usr/bin/env python3
"""G-AX — sympy__sympy-13798.

This bundle consumes NO callee axiom and declares NO A-reference. The behavior
the patch changes — how the two multiplication-separator strings are derived
from the selector — is modeled DEEPLY over the constant separator table
(`mulSymbolTable`) and the selector itself; SPEC_GUIDE §3 forbids axiomatizing a
deeply-modeled changed op. The `axioms` region of Solution.lean is empty.

So G-AX has nothing to validate: it is a skip stub.
"""
import json
import sys

if __name__ == "__main__":
    print(json.dumps({
        "status": "skip",
        "instance": "sympy__sympy-13798",
        "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
                  "(validated by G-CONF)",
    }))
    sys.exit(0)
