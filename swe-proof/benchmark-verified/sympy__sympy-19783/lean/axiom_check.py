#!/usr/bin/env python3
"""G-AX for sympy__sympy-19783 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference. Both
modeled behaviors — `Dagger.__mul__` and `IdentityOperator.__mul__` — are pure
dispatch on the runtime class of the right-hand factor, modeled DEEPLY and
structurally over the finite `Operand`/`Result` carriers (Solution.lean pure
region). SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled changed op, so there
is no callee contract to validate against the real repo. The R legs are validated
by G-CONF.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "sympy__sympy-19783",
    "reason": "no consumed callee axiom and no A-reference; both impls are all R "
              "(validated by G-CONF)",
}))
sys.exit(0)
