#!/usr/bin/env python
"""G-AX for astropy__astropy-8707 — SKIP STUB.

The bundle declares NO callee axioms. The two callees on the changed path
(`bytes.decode('latin1')` and `_pad`) are modeled DEEPLY as `bytesAsText` and
`padCard`, so there is no `axiom <callee>_prop` for the proof to consume.
Nothing to validate.

(Those deep models ARE validated against the real callees by G-CONF /
conformance_check.py, which drives the real patched `Card.fromstring`.)
"""
import sys

print("status=skip no callee axioms declared (decode/_pad modeled deeply)")
sys.exit(0)
