#!/usr/bin/env python3
"""G-AX for sympy__sympy-21379 — skip stub.

The bundle consumes NO unchanged-callee axiom: the two callees
(`extractFactor` ↔ `gcd(p, q)`, `reduceByFactor` ↔ `gcd_terms(i/G, clear=False,
fraction=False)`) are declared as fully abstract `opaque` values, and the proof
of `correct_factorReduce` reasons only about the control flow that routes between
them — it consumes no `_prop` property of either callee's result. There is
therefore no callee contract to validate against the real repo (no `axiom
<callee>_prop` exists). The callees are A-references whose result SHAPE (a factor
on success / a raised PolynomialError signalling inability) is the only thing the
model relies on, and that shape carries no soundness obligation beyond the
`Except` typing already pinned by the spec. SPEC_GUIDE §3 forbids axiomatizing a
function's own behavior, so there is nothing for G-AX to soundness-check.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "sympy__sympy-21379",
    "reason": "no consumed callee axiom and no result-property A-reference; "
              "callees enter fully abstract, proof uses only control flow",
}))
sys.exit(0)
