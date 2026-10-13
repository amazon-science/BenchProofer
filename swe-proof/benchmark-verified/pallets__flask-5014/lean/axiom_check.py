#!/usr/bin/env python
"""G-AX for pallets__flask-5014 — SKIP STUB.

The bundle declares NO callee axioms: the modeled behavior
(`Blueprint.__init__`'s name-validation + name storage) is modeled DEEPLY with
concrete Lean operations (an emptiness test, a dot-membership test, an early
return, a field assignment), so there is no `axiom <callee>_prop` for the proof
to consume. Nothing to validate.

(The deep model IS validated against the real patched `flask.Blueprint` by
G-CONF / conformance_check.py.)
"""
import sys

print("status=skip no callee axioms declared (behavior modeled deeply)")
sys.exit(0)
