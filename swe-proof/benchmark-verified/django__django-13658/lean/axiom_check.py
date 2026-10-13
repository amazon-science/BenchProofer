#!/usr/bin/env python3
"""G-AX for django__django-13658 — SKIP STUB.

The behavior is modeled deeply in Solution.lean (`basename` / `computeProgName`
spell out the path-basename operation and the module-execution special case).
There is no `opaque` callee and no `axiom <callee>_prop` declaration, so there
is nothing for G-AX to validate. The deep model is instead checked against the
real patched program-name computation by G-CONF (conformance_check.py). Exit 0
with status=skip. stdlib-only.
"""
import json
import sys

print(json.dumps({"status": "skip", "reason": "no consumed axioms in bundle"}))
sys.exit(0)
