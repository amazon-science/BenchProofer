#!/usr/bin/env python3
"""G-AX — axiom soundness check.

The modeled function calls NO unchanged opaque callee: the numeric evaluation of
an expression is modeled DEEPLY (`evalSpec` / `implementation_evalf` spell out the
structural recursion over the argument subexpressions and the apply-implementation
step). There is therefore no `opaque <callee>` declaration and no consumed
`axiom <callee>_prop` in Solution.lean, so there is nothing for G-AX to validate.

This is a skip stub (status=skip), per SPEC_GUIDE §4 / the worker contract.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "reason": "no consumed callee axiom: the evaluation is modeled deeply "
              "(no opaque callee, no _prop axiom).",
}))
sys.exit(0)
