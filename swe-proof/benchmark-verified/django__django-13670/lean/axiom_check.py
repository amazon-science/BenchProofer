#!/usr/bin/env python3
"""G-AX for django__django-13670 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference: the
behavior the patch changes — rendering a year as its two-digit short form
(`'%02d' % (year % 100)`) — is modeled DEEPLY as pure integer arithmetic plus
ASCII digit emission (`twoDigitYear` / `digitChar`). It calls no UNCHANGED repo
callee: modulo and `%02d`-formatting are language primitives. SPEC_GUIDE §3
forbids axiomatizing a deeply-modeled changed op, so there is no callee contract
to validate against the real repo. The R/I legs are validated by G-CONF.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "django__django-13670",
    "reason": "no consumed callee axiom and no A-reference; impl is all I/R "
              "(validated by G-CONF)",
}))
sys.exit(0)
