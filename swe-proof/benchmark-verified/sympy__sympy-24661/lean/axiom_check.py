#!/usr/bin/env python3
"""G-AX for sympy__sympy-24661 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference: the
comparison rewrite (rebuilding a recognised relational comparison as an
unevaluated relational call, including the recursive rewriting of its operands)
is modeled DEEPLY and structurally over the parsed-node fragment (`AstNode` /
`transform` / `relClassName`). SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled
changed op, so there is no callee contract to validate against the real repo. The
R/I legs are validated by G-CONF.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "sympy__sympy-24661",
    "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
              "(validated by G-CONF)",
}))
sys.exit(0)
