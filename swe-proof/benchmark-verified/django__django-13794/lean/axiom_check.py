#!/usr/bin/env python3
"""G-AX for django__django-13794 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference. The
single modeled behavior — binary concatenation of operands each of which may be
an on-demand (deferred) value — is modeled DEEPLY: forcing a deferred operand to
its underlying text is `force`, a pure projection of the operand's own carried
text, and the concatenation is ordinary text append. SPEC_GUIDE §3 forbids
axiomatizing a deeply-modeled changed operation, so there is no callee contract
to validate against the real repo. The R/I legs are validated by G-CONF.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "django__django-13794",
    "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
              "(validated by G-CONF)",
}))
sys.exit(0)
