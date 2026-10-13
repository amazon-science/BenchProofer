#!/usr/bin/env python3
"""G-AX for pytest-dev__pytest-10051 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference: the
behaviour the patch changes — emptying the record collector IN PLACE (so the
views taken onto it stay coupled) versus REALLOCATING it (which strands them) —
is modeled DEEPLY as operations on an explicit heap of backing lists
(`cells.set records []`, references preserved), per mapping.md / refinement.md.
SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled changed op, so there is no
callee contract to validate against the real repo. The R legs are validated by
G-CONF.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "pytest-dev__pytest-10051",
    "reason": "no consumed callee axiom and no A-reference; impl is all R "
              "(validated by G-CONF)",
}))
sys.exit(0)
