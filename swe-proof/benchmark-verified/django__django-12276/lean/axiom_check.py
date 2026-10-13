#!/usr/bin/env python3
"""G-AX for django__django-12276 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference: the
required-marker decision is modeled DEEPLY over the observable inputs (the
input's hidden-ness and the truthiness of the initial value). The unchanged base
rule `super().use_required_attribute(initial)` = `not self.is_hidden` is short
and is inlined as the structural term `!isHidden` rather than axiomatized.
SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled changed decision, so there is
no callee contract to validate against the real repo. The R legs are validated by
G-CONF.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "django__django-12276",
    "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
              "(validated by G-CONF)",
}))
sys.exit(0)
