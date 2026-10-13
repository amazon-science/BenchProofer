#!/usr/bin/env python
"""G-AX for scikit-learn__scikit-learn-13439 — SKIP STUB.

The bundle declares NO callee axioms: the one modeled function (the size query of
a sequential composition) is modeled DEEPLY. Reporting the size reads only the
length of the composition's ordered list of steps, spelled out directly in the
Lean impl as `List.length`. There is no `axiom <callee>_prop` for the proof to
consume, so there is nothing to validate.

(The deep model IS validated against the post-patch behavior by G-CONF /
conformance_check.py.)
"""
import sys

print("status=skip no callee axioms declared (behavior modeled deeply)")
sys.exit(0)
