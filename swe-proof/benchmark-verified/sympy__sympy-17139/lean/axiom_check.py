#!/usr/bin/env python3
"""G-AX for sympy__sympy-17139 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference. The
operation the patch changes is a CONTROL-FLOW guard inside `_f` (the per-node
rewrite of `_TR56` in sympy/simplify/fu.py): a new early return when the matching
power's exponent is not real. This changed decision is modeled DEEPLY over the
observable branch queries as the guarded `Id.run do` early-return chain.
SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled changed decision, and §0.7
forbids axiomatizing the function under spec.

The three UNCHANGED operations the bundle touches — the structural matching test,
the realness query, and the exponent-driven rewrite body — are declared as opaque
SIGNATURES only (`isMatchingPow`, `expIsReal`, `transform`); NO `_prop` axiom
asserts any property of them. They appear identically in the spec and the impl,
so they cancel in the differential test and the proof consumes nothing about them.
There is therefore no callee contract to validate against the real repo. The R
legs are validated by G-CONF.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "sympy__sympy-17139",
    "reason": "no consumed callee axiom and no A-reference; the changed op is a "
              "deeply-modeled control-flow guard; opaque callees are "
              "signature-only and cancel in the differential; impl R legs "
              "validated by G-CONF",
}))
sys.exit(0)
