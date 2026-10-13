#!/usr/bin/env python3
"""G-AX for matplotlib__matplotlib-24637 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference: the
draw behavior (`drawTrace`) is modeled DEEPLY as the ordered trace of emitted
renderer operations over the observable flags of the artist (visible,
position-resolvable, has-an-arrow), its class name and its optional group id.
SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled changed behavior, so there is
no callee contract to validate against the real repo. The R legs are validated by
G-CONF.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "matplotlib__matplotlib-24637",
    "reason": "no consumed callee axiom and no A-reference; impl is all R "
              "(validated by G-CONF)",
}))
sys.exit(0)
