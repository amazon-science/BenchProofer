#!/usr/bin/env python
"""G-AX for django__django-16595 — SKIP STUB.

The bundle declares NO callee axioms: the one modeled function
(`AlterField.reduce`) is modeled DEEPLY. The reduction performs only a runtime
kind test of the following operation, a case-insensitive model+field name
comparison, a "no explicit database column" test, and the construction of
replacement operations copying carried-over components — all spelled out
directly in the Lean impl (`String.toLower` equality, an `Option` check, record
literals). There is no `axiom <callee>_prop` for the proof to consume, so there
is nothing to validate.

(The deep model IS validated against the post-patch behavior by G-CONF /
conformance_check.py.)
"""
import sys

print("status=skip no callee axioms declared (behavior modeled deeply)")
sys.exit(0)
