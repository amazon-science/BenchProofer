#!/usr/bin/env python3
"""G-AX for sympy__sympy-20590 — skip stub.

The modeled behaviour (an instance carries a per-instance attribute dictionary
iff some ancestry layer leaves its memory layout open) is a pure conjunction-fold
over the ancestry layers' layout-pinning flags. It invokes NO unchanged repo
callee, so the proof consumes no `axiom <callee>_prop` and there is no
A-reference result property to validate against a real callee. SPEC_GUIDE §3/§4:
with no consumed axiom, G-AX is a skip.

(The real CPython layout semantics ARE exercised — but as the differential
oracle in conformance_check.py / G-CONF, not as an axiom.)

stdlib-only. exit 0.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "sympy__sympy-20590",
    "reason": "no consumed callee axiom and no A-reference result property; the "
              "instance-layout rule is modeled deeply as a pure fold (no repo "
              "callee invoked)",
}))
sys.exit(0)
