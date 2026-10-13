#!/usr/bin/env python3
"""G-AX for sympy__sympy-13091 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference. The
behavior the patch changes — a rich-comparison method ABSTAINING (returning the
NotImplemented singleton) instead of asserting a definite negative for an
operand it cannot interpret, and inequality negating the resolved equality
OPERATOR rather than the raw self-method verdict — is modeled DEEPLY as total
functions over observable boolean inputs (`selfEqVerdict`, `resolveEq`,
`richEqRef`, `richNeRef`). SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled
changed op. The operand's reflected opinion is arbitrary external user code (a
free input, `otherVerdict`), not a repo callee, so there is no callee contract to
validate. The R legs are validated by G-CONF.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "sympy__sympy-13091",
    "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
              "(validated by G-CONF)",
}))
sys.exit(0)
