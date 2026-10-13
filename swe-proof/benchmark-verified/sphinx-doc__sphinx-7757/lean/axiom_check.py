#!/usr/bin/env python
"""G-AX for sphinx-doc__sphinx-7757 — SKIP STUB.

The bundle declares NO callee axioms: the one modeled behavior (aligning the
supplied default-value expressions onto the positional parameters of a parsed
signature, in `signature_from_str`) is modeled DEEPLY. It reads only
directly-supplied observations — the count of positional-only parameters, the
count of positional-or-keyword parameters, and the list of default-expression
texts — all spelled out in the Lean impl (a left-pad of the defaults list up to
the positional count). The default-expression renderer and the `Parameter`
constructor are subsumed into the `List String` input and the `Option String`
result (mapping.md), not consumed via an `axiom <callee>_prop`. There is nothing
to validate.

(The deep model IS validated against the post-patch behavior by G-CONF /
conformance_check.py.)
"""
import sys

print("status=skip no callee axioms declared (behavior modeled deeply)")
sys.exit(0)
