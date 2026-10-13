#!/usr/bin/env python3
"""G-AX for matplotlib__matplotlib-25287 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference. The
modeled decision (the offset-text color for each axis) reads two rcParams
(`*tick.color`, `*tick.labelcolor`) as plain data and performs a pure inline
two-way choice (the `'inherit'`-sentinel test), modeled deeply as `Option.getD`.
There is therefore no callee contract to validate against the real repo.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "matplotlib__matplotlib-25287",
    "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
              "(validated by G-CONF)",
}))
sys.exit(0)
