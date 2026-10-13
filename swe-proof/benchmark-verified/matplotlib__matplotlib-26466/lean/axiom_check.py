#!/usr/bin/env python3
"""G-AX for matplotlib__matplotlib-26466 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference: the
modeled behaviour (capturing a 2D coordinate by value at construction time,
decoupled from later mutation of the source) is modeled DEEPLY as a direct
component-wise snapshot. SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled
changed behaviour, so there is no callee contract to validate against the real
repo. The R legs are validated by G-CONF.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "matplotlib__matplotlib-26466",
    "reason": "no consumed callee axiom and no A-reference; impl is all R "
              "(validated by G-CONF)",
}))
sys.exit(0)
