#!/usr/bin/env python3
"""G-AX for sphinx-doc__sphinx-9461 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference: the
behavior the patch changes — which leading modifier words are rendered before a
documented read-only attribute, and in what order — is modeled DEEPLY as a pure
string-building function over the two observable toggles (the abstract flag and
the class-level flag). SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled
changed op, so there is no callee contract to validate against the real repo.
The R/I legs are validated by G-CONF.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "sphinx-doc__sphinx-9461",
    "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
              "(validated by G-CONF)",
}))
sys.exit(0)
