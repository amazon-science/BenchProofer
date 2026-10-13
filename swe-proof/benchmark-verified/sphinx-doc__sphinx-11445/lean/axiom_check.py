#!/usr/bin/env python3
"""G-AX for sphinx-doc__sphinx-11445 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO `opaque` callee:
the operation the patch changes — the classifier that decides which leading
lines of the document body are bibliographic field lines, and the placement of
the preamble relative to them — is modeled DEEPLY as a pure character-level
matcher (`fieldMarkerScan` / `isFieldLine`) plus list-splice arithmetic over the
input lines. SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled changed op, so
there is no callee contract to validate against the real repo.

The field-line classifier is an A-reference (a deep model of the unchanged
docutils `field_marker` grammar the post-patch code consults); it is validated
== the REAL compiled docutils regex by G-CONF (conformance_check.py LEG 1), not
by an axiom. The full R/I/A-reference impl is validated by G-CONF LEG 2.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "sphinx-doc__sphinx-11445",
    "reason": "no consumed callee axiom and no opaque decl; the changed "
              "classifier is modeled deeply (A-reference) and validated against "
              "the real docutils field_marker grammar by G-CONF",
}))
sys.exit(0)
