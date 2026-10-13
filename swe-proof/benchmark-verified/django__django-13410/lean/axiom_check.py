#!/usr/bin/env python
"""G-AX for django__django-13410 — SKIP STUB.

The bundle declares NO callee axioms. The lower-level locking primitive
(`fcntl.flock`) is not axiomatized: its result is abstracted as the `outcome`
argument (the value/`ok` channel vs. the out-of-band/`error` channel), and the
only logic modeled is the pure transformation of that result into a boolean
status. There is no `axiom <callee>_prop` for the proof to consume — the
correctness proofs close with zero axioms.

The behavioral claim (status as a function of the primitive's result channel) is
validated against the REAL patched `locks.lock`/`locks.unlock` by G-CONF /
conformance_check.py, which drives them in-container with a substituted `flock`.
"""
import sys

print("status=skip no callee axioms declared (flock abstracted as `outcome`)")
sys.exit(0)
