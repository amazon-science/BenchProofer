#!/usr/bin/env python3
"""G-AX for sympy__sympy-17318 — skip stub.

The bundle consumes NO unchanged-callee axiom. The genuinely-changed op (the
guard that selects between the two decomposition routines) is modeled DEEPLY as
`allSquarePosRat` (exact rational arithmetic), so it is R-content checked by
G-CONF, not an axiom. The two routines the guard selects between
(`fastDecomp` <-> `split_surds`, `depthMatch` <-> the depth-based matcher) are
declared as fully abstract `opaque` values, and the proof of `correct_decompose`
reasons only about the branch selection that routes between them — it consumes no
`_prop` property of either callee's result. There is therefore no callee contract
to validate against the real repo (no `axiom <callee>_prop` exists). SPEC_GUIDE
§3 forbids axiomatizing a function's own behavior, so there is nothing for G-AX
to soundness-check.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "sympy__sympy-17318",
    "reason": "no consumed callee axiom; the changed guard is deep-modeled (R, "
              "checked by G-CONF) and the two branch routines enter fully "
              "abstract, proof uses only branch selection",
}))
sys.exit(0)
