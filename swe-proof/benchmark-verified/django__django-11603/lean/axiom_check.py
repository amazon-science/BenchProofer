#!/usr/bin/env python
"""G-AX for django__django-11603 — SKIP STUB.

The bundle declares NO callee axioms: the modeled behavior
(`Aggregate.__init__`'s distinct-validation + flag storage, with the per-class
`allow_distinct` policy) is modeled DEEPLY with concrete Lean operations, so
there is no `axiom <callee>_prop` for the proof to consume. Nothing to validate.

(The deep model IS validated against the real patched aggregate classes by
G-CONF / conformance_check.py.)
"""
import sys

print("status=skip no callee axioms declared (behavior modeled deeply)")
sys.exit(0)
