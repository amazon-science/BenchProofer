#!/usr/bin/env python
"""G-AX for django__django-16801 — SKIP STUB.

The bundle declares NO callee axioms: the one modeled function (the decision in
`ImageField.contribute_to_class` of whether to install the post-initialization
dimension-sync handler) is modeled DEEPLY. The decision reads only three
already-available facts — a concrete/abstract flag and the two optional
attribute names the field tracks — and combines them with boolean connectives
and a non-empty-name test, all spelled out directly in the Lean impl (`Bool`
operations, an `Option`/non-empty-string test). There is no `axiom <callee>_prop`
for the proof to consume, so there is nothing to validate.

(The deep model IS validated against the post-patch behavior by G-CONF /
conformance_check.py.)
"""
import sys

print("status=skip no callee axioms declared (behavior modeled deeply)")
sys.exit(0)
