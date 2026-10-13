#!/usr/bin/env python3
"""G-AX for django__django-13925 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference. The
modeled function (`_check_default_pk`) is a pure decision over boolean
observations of the model class — whether its primary key was auto-created,
whether the primary key is a to-one relation, whether that relation links the
model to a parent it extends, and whether a default primary-key type was opted
into at the project or application level — together with the advisory's
message/hint/identifier text. Every one of those is read as plain input data
(mapping.md), and the added parent-link guard is modeled DEEPLY as a boolean
conjunction, not axiomatized (SPEC_GUIDE §3 forbids axiomatizing the changed
op). So there is no callee contract to validate against the real repo. The R/I
legs are validated by G-CONF (`conformance_check.py`).
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "django__django-13925",
    "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
              "(validated by G-CONF)",
}))
sys.exit(0)
