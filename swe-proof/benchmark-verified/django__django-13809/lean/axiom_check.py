#!/usr/bin/env python3
"""G-AX — axiom soundness check for django__django-13809.

This bundle consumes NO callee axiom: the startup routine's observable behavior
is modeled DEEPLY as the ordered list of actions it emits, gated on a boolean
control (SPEC_GUIDE §3 — a deeply-modeled changed decision is never
axiomatized). There is therefore no `axiom <callee>_prop` whose property a real
callee must be checked against. G-AX is a no-op skip.
"""
import sys

if __name__ == "__main__":
    print("status=skip")
    print("no axioms consumed by the bundle (deep structural model; no callee contract)")
    sys.exit(0)
