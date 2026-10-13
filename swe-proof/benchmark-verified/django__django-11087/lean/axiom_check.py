#!/usr/bin/env python3
"""G-AX for django__django-11087 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference: the
modeled decision (`collectFieldSelection`) is all R/I (validated by G-CONF). The
two guard flags and the column-name lists enter as plain data, and the gather of
referenced columns is modeled deeply as list flatten + dedup. There is therefore
no callee contract to validate against the real repo.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "django__django-11087",
    "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
              "(validated by G-CONF)",
}))
sys.exit(0)
