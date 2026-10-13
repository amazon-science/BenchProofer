#!/usr/bin/env python3
"""G-AX for django__django-15127 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference: the
modeled decision (`resolveTagMap`) is all R/I (validated by G-CONF). The change
indicator enters as a Bool; the defaults, overrides, and previously-cached
mapping enter as plain data; and the combination of defaults + overrides into the
effective mapping is modeled deeply as an assoc-list concatenation (override-wins
under first-match lookup). There is therefore no callee contract to validate
against the real repo.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "django__django-15127",
    "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
              "(validated by G-CONF)",
}))
sys.exit(0)
