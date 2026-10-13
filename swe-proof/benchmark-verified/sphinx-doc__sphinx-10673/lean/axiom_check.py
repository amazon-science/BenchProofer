#!/usr/bin/env python
"""G-AX for sphinx-doc__sphinx-10673 — SKIP STUB.

The bundle declares NO callee axioms: the one modeled behavior (the accepted-entry
loop of the table-of-contents directive's content parser) is modeled DEEPLY. The
decision reads only directly-supplied observations — the directive's body lines,
the set of names of the documents the project contains, and the fixed set of
names of the builder-generated reference pages (the general index, the module
index, the search page) — and computes acceptance with a string blank-test and a
list/set membership test, all spelled out directly in the Lean impl
(`Id.run do` accumulator loop, `String == ""`, `List.contains` over a list
append). There is no `axiom <callee>_prop` for the proof to consume, so there is
nothing to validate.

(The deep model IS validated against the post-patch behavior by G-CONF /
conformance_check.py.)
"""
import sys

print("status=skip no callee axioms declared (behavior modeled deeply)")
sys.exit(0)
