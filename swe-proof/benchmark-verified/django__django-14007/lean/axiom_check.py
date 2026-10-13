#!/usr/bin/env python3
"""G-AX for django__django-14007 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference: the
behaviour the patch adds — passing the rows a creating write returns through each
returning field's converter chain — is modeled DEEPLY (`convertRow` /
`applyChain` / `anyConverter`) over grounded inputs (the candidate raw rows from
the three backend pathways and the per-field converter chains). SPEC_GUIDE §3
forbids axiomatizing a deeply-modeled changed op, so there is no callee contract
to validate against the real repo. The R legs are validated by G-CONF.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "django__django-14007",
    "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
              "(validated by G-CONF)",
}))
sys.exit(0)
