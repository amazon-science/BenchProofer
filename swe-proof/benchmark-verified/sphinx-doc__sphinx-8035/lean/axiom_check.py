#!/usr/bin/env python
"""G-AX for sphinx-doc__sphinx-8035 — SKIP STUB.

The bundle declares NO callee axioms: the one modeled decision (the private-member
arm of `Documenter.filter_members`) is modeled DEEPLY. The decision reads only
directly-supplied observations — the shape of the `:private-members:` selection
(None / ALL / a list of names), whether the member is documented, whether
undocumented members are being kept, the member's own name, list membership of
that name, and the already-computed inherited-member boolean — all spelled out
directly in the Lean impl (a `match` on the option tag, an `Option`/list
membership test, boolean guards). There is no `axiom <callee>_prop` for the proof
to consume, so there is nothing to validate.

(The deep model IS validated against the post-patch behavior by G-CONF /
conformance_check.py.)
"""
import sys

print("status=skip no callee axioms declared (behavior modeled deeply)")
sys.exit(0)
