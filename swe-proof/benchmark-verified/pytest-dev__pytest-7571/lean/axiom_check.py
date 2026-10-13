#!/usr/bin/env python3
"""G-AX for pytest-dev__pytest-7571 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference: the
behavior the patch changes — recording, on each threshold raise, the level in
effect just before it, and re-applying the last such record at teardown — is
modeled DEEPLY over the observable inputs (the initial capture-handler level and
the ordered sequence of raised levels). SPEC_GUIDE §3 forbids axiomatizing a
deeply-modeled changed op, so there is no callee contract to validate against the
real repo. The R/I legs are validated by G-CONF.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "pytest-dev__pytest-7571",
    "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
              "(validated by G-CONF)",
}))
sys.exit(0)
