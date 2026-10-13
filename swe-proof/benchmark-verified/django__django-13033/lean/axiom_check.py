#!/usr/bin/env python
"""G-AX for django__django-13033 — SKIP STUB.

The bundle declares NO callee axioms: the one modeled function (the
default-ordering-expansion guard in `SQLCompiler.find_ordering_name`) is modeled
DEEPLY. The guard reads four already-resolved observations (the field's
relation flag, the related model's ordering flag, the field's stored-attribute
name, and the lookup path) and computes the path's final `'__'`-separated
segment directly — all spelled out in the Lean impl (`String.splitOn` /
`getLastD`, `Option`/`String` (in)equality). There is no `axiom <callee>_prop`
for the proof to consume, so there is nothing to validate.

(The deep model IS validated against the post-patch behavior by G-CONF /
conformance_check.py.)
"""
import sys

print("status=skip no callee axioms declared (behavior modeled deeply)")
sys.exit(0)
