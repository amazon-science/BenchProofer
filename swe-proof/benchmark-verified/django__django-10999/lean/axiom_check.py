#!/usr/bin/env python3
"""G-AX for django__django-10999 — SKIP STUB.

The bundle consumes NO callee axiom. The only `opaque` declaration
(`fallbackFormatMicros`, the unchanged ISO-8601 / PostgreSQL alternative
interpreter) is an A-REFERENCE: it is validated by G-CONF (the conformance shadow
leaves it as the real alternative-format parsing of `parse_duration`), not by a
consumed `axiom <callee>_prop`. The changed standard-format branch is modeled
DEEPLY (`primaryFormatMicros`), so it is not axiomatized either.

Therefore there is no axiom property to validate here. Exit 0 with status=skip.
"""
import json
import sys

print(json.dumps({
    "gate": "G-AX",
    "status": "skip",
    "reason": "no consumed callee axiom; the single opaque is an A-reference validated by G-CONF",
}))
sys.exit(0)
