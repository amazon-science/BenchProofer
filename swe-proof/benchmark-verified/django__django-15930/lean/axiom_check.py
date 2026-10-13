#!/usr/bin/env python3
"""G-AX for django__django-15930 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference: the
modeled decision (`resolveBranchCondition`) is all R/I (validated by G-CONF). The
rendered guard fragment, its parameters, and the always-satisfied stand-in's
fragment + parameters all enter as plain data; the only operation is the
empty-string test on the guard fragment plus a wholesale substitution. There is
therefore no callee contract to validate against the real repo.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "django__django-15930",
    "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
              "(validated by G-CONF)",
}))
sys.exit(0)
