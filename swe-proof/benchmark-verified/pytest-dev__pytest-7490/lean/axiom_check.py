#!/usr/bin/env python3
"""G-AX for pytest-dev__pytest-7490 — skip stub.

The impl region is all R/I (refinement.md): the modeled operation is the
most-specific-known-first selection between two annotation observations, spelled
out directly. No unchanged callee is consumed as an axiom and there is no
A-reference deep model. Soundness of the R/I legs is established mechanically by
conformance_check.py (G-CONF). Hence there is nothing for G-AX to validate.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "pytest-dev__pytest-7490",
    "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
              "(validated by G-CONF)",
}))
sys.exit(0)
