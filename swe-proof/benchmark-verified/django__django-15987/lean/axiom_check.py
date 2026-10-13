#!/usr/bin/env python
"""G-AX for django__django-15987 — SKIP STUB.

The bundle declares NO callee axioms: the changed behavior (the per-app
default-fixtures-directory collision check in `Command.fixture_dirs`) is modeled
DEEPLY with concrete Lean operations — a textual-equality membership test
(`collides`) and a first-match scan (`List.find?`). There is no
`axiom <callee>_prop` for the proof to consume, so there is nothing to validate.

(The deep model IS validated against the real patched callee by G-CONF /
conformance_check.py.)
"""
import sys

print("status=skip no callee axioms declared (behavior modeled deeply)")
sys.exit(0)
