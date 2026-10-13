#!/usr/bin/env python3
"""G-AX for sympy__sympy-22456 — skip stub.

The modeled behaviour (the argument-reconstruction round-trip
`expr.func(*expr.args) == expr` of the atomic string value) is modeled DEEPLY in
the impl: the reconstruction callable applied to the value's positional argument
list is spelled out as "yield the value itself". It invokes NO unchanged repo
callee whose property the proof must assume — there is no consumed
`axiom <callee>_prop` and no A-reference result property to validate against an
outside callee. SPEC_GUIDE §3/§4: with no consumed axiom, G-AX is a skip.

(The REAL patched `String.func`/`String.args` round-trip IS exercised — but as
the differential oracle in conformance_check.py / G-CONF, not as an axiom.)

stdlib-only. exit 0.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "sympy__sympy-22456",
    "reason": "no consumed callee axiom and no A-reference result property; the "
              "argument-reconstruction round-trip is modeled deeply (no outside "
              "repo callee is assumed). The real round-trip is validated by "
              "G-CONF instead.",
}))
sys.exit(0)
