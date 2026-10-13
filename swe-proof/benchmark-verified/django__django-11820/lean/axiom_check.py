#!/usr/bin/env python3
"""G-AX for django__django-11820 — SKIP STUB.

The bundle consumes NO callee axiom: the two fixed behaviors (the pk-alias
resolution and the non-relation walk termination) are modeled concretely (I),
and the model-graph operations (by-name field resolution, relation target,
transform admissibility) are A-reference data validated against the real callees
by G-CONF (conformance_check.py), not consumed as proof axioms. There is thus no
`axiom <callee>_prop` to check here.
"""
import sys

print("skip: no consumed axioms (status=skip)")
sys.exit(0)
