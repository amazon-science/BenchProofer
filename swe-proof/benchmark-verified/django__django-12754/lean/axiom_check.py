#!/usr/bin/env python
"""G-AX for django__django-12754 — SKIP STUB.

The bundle declares NO callee axioms: the one modeled function (the per-model
ordering-dependency construction inside `generate_created_models`) is modeled
DEEPLY. Every operation — splitting a dotted base reference, the set
difference/intersection over field-name collections, the membership tests, and
the construction of dependency tuples — is spelled out directly in the Lean impl
over `List`/`Option`/`String`. There is no `axiom <callee>_prop` for the proof
to consume, so there is nothing to validate here.

(The deep model IS validated against the post-patch behavior by G-CONF /
conformance_check.py.)
"""
import sys

print("status=skip no callee axioms declared (behavior modeled deeply)")
sys.exit(0)
