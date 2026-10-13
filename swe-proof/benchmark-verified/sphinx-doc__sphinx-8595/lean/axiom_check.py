#!/usr/bin/env python3
"""G-AX for sphinx-doc__sphinx-8595 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference: the
behavior the patch changes — distinguishing an absent export list from a
declared-but-empty one when selecting which module members to document — is
modeled DEEPLY over the observable inputs (the export list as an `Option`, the
discovered member names, the requested names). SPEC_GUIDE §3 forbids
axiomatizing a deeply-modeled changed op, so there is no callee contract to
validate against the real repo. The R legs are validated by G-CONF.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "sphinx-doc__sphinx-8595",
    "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
              "(validated by G-CONF)",
}))
sys.exit(0)
