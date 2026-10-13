#!/usr/bin/env python3
"""G-AX for matplotlib__matplotlib-23299 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference: the
behavior the patch changes — which keys the scoped settings manager's restore
reverts — is modeled DEEPLY as pure association-list operations (`dictUpdate`,
`assocErase`, `assocSet`) over the observable mapping values (`orig`, `final`).
SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled changed op, so there is no
callee contract to validate against the real repo. The R legs are validated by
G-CONF.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "matplotlib__matplotlib-23299",
    "reason": "no consumed callee axiom and no A-reference; impl is all R "
              "(validated by G-CONF)",
}))
sys.exit(0)
