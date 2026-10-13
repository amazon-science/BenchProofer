#!/usr/bin/env python
"""G-AX for django__django-13513 — SKIP STUB.

The bundle declares NO callee axioms: the one modeled function
(`ExceptionReporter.get_traceback_frames`) is modeled DEEPLY — the changed
control flow (process every chain link and concatenate its frames, rather than
abandoning the walk at the first link with an empty traceback) is spelled out as
a concrete list concatenation over the per-link frame sequences. There is no
`axiom <callee>_prop` for the proof to consume, so there is nothing to validate.

(The deep model IS validated against the post-patch behavior by G-CONF /
conformance_check.py.)
"""
import sys

print("status=skip no callee axioms declared (behavior modeled deeply)")
sys.exit(0)
