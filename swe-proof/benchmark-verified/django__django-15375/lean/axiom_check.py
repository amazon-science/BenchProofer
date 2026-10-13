#!/usr/bin/env python3
"""G-AX for django__django-15375 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference: the
modeled decision (`resolveAggregate`) is all R/I (validated by G-CONF). The two
observables (whether the aggregate is resolved as a terminal aggregation, and
whether a fallback value was supplied) enter as plain data, and constructing the
coalescing wrapper plus propagating the terminal marker are modeled directly.
There is therefore no callee contract to validate against the real repo.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "django__django-15375",
    "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
              "(validated by G-CONF)",
}))
sys.exit(0)
