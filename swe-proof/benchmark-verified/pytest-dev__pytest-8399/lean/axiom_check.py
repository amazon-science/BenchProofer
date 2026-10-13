#!/usr/bin/env python3
"""G-AX for pytest-dev__pytest-8399 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference: the
generated fixture name is built entirely from string literals and the two string
inputs (the setup-hook name and the owning object's qualified name) by
concatenation, with a leading underscore prepended (the fix). There is no
unchanged repo callee in the modeled op, so there is no callee contract to
validate against the real repo. The R/I legs are validated by G-CONF.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "pytest-dev__pytest-8399",
    "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
              "(validated by G-CONF)",
}))
sys.exit(0)
