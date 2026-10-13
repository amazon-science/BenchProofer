#!/usr/bin/env python3
"""G-AX for pytest-dev__pytest-5787 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference: both
modeled routines (serialization and deserialization of a failure
representation) are modeled DEEPLY over the observable data — the chain of links,
the section list, and the outermost traceback/crash. The only sub-operation the
fix leaves unchanged (the per-frame entry-payload copy) is modeled as the
identity over the abstracted payload (`packLink`/`unpackLink`), not as an
axiomatized callee. SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled op, so
there is no callee contract to validate against the real repo. The R legs are
validated by G-CONF.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "pytest-dev__pytest-5787",
    "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
              "(validated by G-CONF)",
}))
sys.exit(0)
