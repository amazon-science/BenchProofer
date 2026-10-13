#!/usr/bin/env python
"""G-AX for django__django-13964 — SKIP STUB.

The bundle declares NO callee axioms: the one modeled behavior (the foreign-key
key-value adoption decision in `Model._prepare_related_fields_for_save`) is
modeled DEEPLY. It computes only (a) an emptiness test on the stored scalar key
value (membership in `field.empty_values`, restricted to the reachable scalar
members `None` and the empty string, modeled as `fkValueIsEmpty`), and (b) the
adoption of the related object's primary key (a direct assignment). Both are
spelled out directly in the Lean `pure`/`impl` regions. There is no
`axiom <callee>_prop` for the proof to consume, so there is nothing to validate.

(The deep model IS validated against the post-patch behavior by G-CONF /
conformance_check.py.)
"""
import sys

print("status=skip no callee axioms declared (behavior modeled deeply)")
sys.exit(0)
