#!/usr/bin/env python3
"""G-AX for django__django-11095 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference: the
modeled function (`getInlineInstances`) is all R/I (validated by G-CONF). The
selected-inline-class list (`hookInlines`), the three per-editor permission
outcomes, and the editor identity all enter as plain data; the filtering and
max-rows-zeroing logic is modeled deeply. There is therefore no callee contract
to validate against the real repo.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "django__django-11095",
    "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
              "(validated by G-CONF)",
}))
sys.exit(0)
