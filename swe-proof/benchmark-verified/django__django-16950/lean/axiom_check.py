#!/usr/bin/env python3
"""G-AX for django__django-16950 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference: the
reset decision (`shouldReset`) is modeled DEEPLY over four boolean observables of
the situation (`adding`, `hasDefault`, `isParentPk`, `hasFormData`) and the
attribute's opaque current value, which enters as plain data. SPEC_GUIDE §3
forbids axiomatizing a deeply-modeled changed decision, so there is no callee
contract to validate against the real repo. The R/I legs are validated by
G-CONF.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "django__django-16950",
    "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
              "(validated by G-CONF)",
}))
sys.exit(0)
