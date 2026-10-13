#!/usr/bin/env python
"""G-AX for django__django-13343 — SKIP STUB.

The bundle declares NO callee axioms: both changed functions
(`FileField.__init__` storage resolution; `FileField.deconstruct` storage-kwarg
decision) are modeled DEEPLY with concrete Lean operations, so there is no
`axiom <callee>_prop` for the proof to consume. Nothing to validate.

(The deep models ARE validated against the real callees by G-CONF
/ conformance_check.py.)
"""
import sys

print("status=skip no callee axioms declared (both behaviors modeled deeply)")
sys.exit(0)
