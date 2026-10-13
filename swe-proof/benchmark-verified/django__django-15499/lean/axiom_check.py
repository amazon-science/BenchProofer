#!/usr/bin/env python3
"""G-AX for django__django-15499 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference: the
modeled decision (`optimizeCreateThenAlterManagers`) is all R/I (validated by
G-CONF). The reduction performs only a case-insensitive model-name comparison
(modeled deeply as `String.toLower`) and the construction of a fresh creation
step copying four components and substituting the managers (modeled deeply as a
structure update). There is therefore no callee contract to validate against the
real repo.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "django__django-15499",
    "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
              "(validated by G-CONF)",
}))
sys.exit(0)
