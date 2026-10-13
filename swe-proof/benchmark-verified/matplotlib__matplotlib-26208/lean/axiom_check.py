#!/usr/bin/env python3
"""G-AX for matplotlib__matplotlib-26208 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference. The
only behavior the patch changes — the newly-created twin frame inheriting its
shared axis's per-axis interpretation configuration — is a plain attribute copy,
modeled DEEPLY as `Option Nat` data on the frame structure (`Axis.units`,
`Axes`). SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled changed op, so there
is no callee contract to validate against the real repo. The R legs are validated
by conformance_check.py (G-CONF).
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "matplotlib__matplotlib-26208",
    "reason": "no consumed callee axiom and no A-reference; the changed op is a "
              "deeply-modeled attribute copy, all R (validated by G-CONF)",
}))
sys.exit(0)
