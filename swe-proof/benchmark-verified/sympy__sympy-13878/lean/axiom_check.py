#!/usr/bin/env python3
"""G-AX for sympy__sympy-13878.

The bundle consumes NO callee axiom: the arcsin CDF closed form is modeled
deeply with Mathlib `Real.arcsin` / `Real.sqrt` / `Real.pi` (see
refinement.md — no A-consumed rows, no `opaque` callee, no `_prop` axiom).
There is therefore nothing for G-AX to validate. Emit a skip status.
"""
import json
import sys

print(json.dumps({"status": "skip",
                  "reason": "no consumed callee axiom (closed form modeled deeply)"}))
sys.exit(0)
