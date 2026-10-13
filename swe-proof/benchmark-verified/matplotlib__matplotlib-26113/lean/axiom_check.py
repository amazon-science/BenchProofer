#!/usr/bin/env python3
"""G-AX for matplotlib__matplotlib-26113 — skip stub.

The bundle consumes NO `_prop` callee axiom. The behavior the patch changes — the
per-cell keep test `len(acc) >= mincnt` — is modeled DEEPLY in exact integer
arithmetic; SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled changed op.

The only opaque callee, `reduceC` (the user-supplied `reduce_C_function`), is
applied IDENTICALLY in `problem_spec` and `implementation`, so it cancels in the
correctness proof and no property of it is asserted. It is an arbitrary user
callable, not pinned by the fix, so there is no callee contract to validate
against the real repo. The R legs are validated by G-CONF.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "matplotlib__matplotlib-26113",
    "reason": "no consumed callee axiom; the one opaque callee (reduce_C_function) "
              "is applied identically in spec and impl and asserts no property; "
              "impl is all R (validated by G-CONF)",
}))
sys.exit(0)
