#!/usr/bin/env python3
"""G-AX for django__django-15731 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference: the
modeled behavior (`delegateMetadata`) is all R/I (validated by G-CONF). The
underlying method's metadata and the bare wrapper's placeholder metadata enter as
plain data, and the metadata propagation (`functools.wraps`'s observable effect)
is modeled deeply as a field-by-field copy of the metadata carrier. There is
therefore no callee contract to validate against the real repo.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "django__django-15731",
    "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
              "(validated by G-CONF)",
}))
sys.exit(0)
