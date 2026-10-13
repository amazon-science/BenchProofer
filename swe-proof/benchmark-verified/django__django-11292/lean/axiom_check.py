#!/usr/bin/env python3
"""G-AX for django__django-11292 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference: the
modeled launch decision (`runCommand`) is all R (validated by G-CONF). Whether a
command performs system checks and whether the launch asked to skip them enter as
plain data (`commandPerformsChecks` / `skipRequested`); the registration of the
skip option and the post-patch check gate are modeled deeply over that data, and
the system-check routine (`self.check()`) is observed only as WHETHER it runs
(`ranChecks` vs `skippedChecks`). There is therefore no callee contract to
validate against the real repo.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "django__django-11292",
    "reason": "no consumed callee axiom and no A-reference; impl is all R "
              "(validated by G-CONF)",
}))
sys.exit(0)
