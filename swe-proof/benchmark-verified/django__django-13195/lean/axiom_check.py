#!/usr/bin/env python3
"""G-AX for django__django-13195 — skip stub.

The bundle consumes NO unchanged-callee `_prop` axiom. The changed deletion
decision (force `secure` when the key prefix OR the cross-site `none` policy
applies, and forward the policy to the cookie-construction primitive) is modeled
DEEPLY over the deletion arguments (`deleteSecure` + `setCookie`). SPEC_GUIDE §3
forbids axiomatizing a deeply-modeled changed op, so there is no callee contract
to validate against the real repo. The R / A-reference legs are validated by
G-CONF (conformance_check.py).
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "django__django-13195",
    "reason": "no consumed callee axiom and no A-reference _prop; the changed "
              "decision is modeled deeply (all R), validated by G-CONF",
}))
sys.exit(0)
