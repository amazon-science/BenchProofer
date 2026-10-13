#!/usr/bin/env python
"""G-AX for django__django-16145 — SKIP STUB.

The bundle declares NO callee axioms: the one modeled function (the banner
display-address computation in `runserver`'s `inner_run`) is modeled DEEPLY —
the displayed host is spelled out as a concrete three-way expression over the
resolved bind host and the raw-IPv6 flag (bracket-wrap, shorthand-to-dotted, or
verbatim), using only string equality, concatenation, and two literals. There is
no `axiom <callee>_prop` for the proof to consume, so there is nothing to
validate.

(The deep model IS validated against the post-patch behavior by G-CONF /
conformance_check.py.)
"""
import sys

print("status=skip no callee axioms declared (behavior modeled deeply)")
sys.exit(0)
