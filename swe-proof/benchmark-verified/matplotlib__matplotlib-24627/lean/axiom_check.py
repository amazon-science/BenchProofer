#!/usr/bin/env python3
"""G-AX for matplotlib__matplotlib-24627 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference: the
child-clearing behavior is modeled DEEPLY as a pure list/record transformation
(empty the child list; set each former child's owning axes/figure references to
none, preserving every other field). SPEC_GUIDE §3 forbids axiomatizing a
deeply-modeled changed operation, so there is no callee contract to validate
against the real repo. The R legs are validated by G-CONF.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "matplotlib__matplotlib-24627",
    "reason": "no consumed callee axiom and no A-reference; impl is all R "
              "(validated by G-CONF)",
}))
sys.exit(0)
