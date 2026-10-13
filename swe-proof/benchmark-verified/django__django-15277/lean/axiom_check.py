#!/usr/bin/env python
"""G-AX for django__django-15277 — SKIP STUB.

The bundle declares NO callee axioms: the modeled behavior (`CharField.__init__`'s
guarded attachment of a length-bound validator to the field's validator list) is
modeled DEEPLY with concrete Lean operations — the conditional `++` append of a
`Validator.lengthBound` carrying the declared length. The length-bound
validator's CONSTRUCTION is the operation the fix gates, so it is modeled, not
axiomatized; there is no `axiom <callee>_prop` for the proof to consume.

(The deep model IS validated against the real patched `__init__` list-construction
behavior by G-CONF / conformance_check.py.)
"""
import sys

print("status=skip no callee axioms declared (behavior modeled deeply)")
sys.exit(0)
