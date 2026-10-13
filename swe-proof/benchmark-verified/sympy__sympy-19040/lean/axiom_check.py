#!/usr/bin/env python3
"""G-AX for sympy__sympy-19040 — skip stub.

The bundle consumes NO unchanged-callee axiom. Every polynomial-algebra callee
(`groundLC`, `groundMonic`, `degreeList`, `sqfPart`, `sqfNorm`,
`factorListInclude`, `raiseShift`, `recoverOne`, `trialDivision`) is declared as
a fully abstract `opaque` value, and the proof of `correct_extFactor` reasons
only about the data flow that routes results among them (plus one list-shape
induction equating the recovery `for`-loop with the `recoverLoop` front-recursive
fold). It consumes no `_prop` property of any callee's result, so no
`axiom <callee>_prop` exists to validate against the real repo.

SPEC_GUIDE §3 forbids axiomatizing a function's own behaviour; the callees are
A-references whose result SHAPE (the tuple/list typing) is all the model relies
on, and that shape carries no soundness obligation beyond the typing already
pinned by the spec. There is therefore nothing for G-AX to soundness-check.

If the proof agent later proposes a `_prop` axiom (axiom-propose loop), this stub
must be replaced with a real in-container check of that property against the named
real callee.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "sympy__sympy-19040",
    "reason": "no consumed callee axiom; all callees enter fully abstract, proof "
              "uses only data routing + a list-shape induction",
}))
sys.exit(0)
