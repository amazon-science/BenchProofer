#!/usr/bin/env python3
"""G-AX for sphinx-doc__sphinx-8638 — skip stub.

The bundle consumes NO unchanged-callee axiom: the `proof` region of
`correct_renderVariableItem` needs no property of an opaque callee. The
role-application callee (`Field.make_xref` in `sphinx/util/docfields.py`) is
modeled DEEPLY as the pure helper `makeXref` (the `not rolename` plain branch +
the cross-reference branch). It appears IDENTICALLY in the specification and the
implementation, so it is an A-reference that cancels in the differential test
(G-CONF) rather than a consumed `axiom … _prop`. SPEC_GUIDE §3 forbids
axiomatizing a deeply-modeled op. The soundness-critical decision the patch
changes — the variable NAME's cross-reference role flipping from "obj" to empty,
so the name renders as a plain strong token — is pinned structurally by the
spec. There is therefore no callee contract to validate against the real repo.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "sphinx-doc__sphinx-8638",
    "reason": "no consumed callee axiom; the role-application callee make_xref "
              "is an A-reference modeled deeply and identical in spec and impl "
              "(validated by G-CONF)",
}))
sys.exit(0)
