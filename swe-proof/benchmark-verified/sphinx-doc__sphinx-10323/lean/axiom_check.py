#!/usr/bin/env python3
"""G-AX for sphinx-doc__sphinx-10323 — skip stub.

The bundle consumes NO unchanged-callee axiom: the `proof` region of
`correct_assembleLines` needs no property of the opaque callees
(`selectContent`, `dedentCore`). Both appear IDENTICALLY in the specification and
the implementation, so they are A-references that cancel in the differential test
rather than consumed `axiom … _prop`. The soundness-critical behaviour the patch
changes — the ORDER in which the de-indentation runs relative to the
author-supplied prepend/append lines — is modeled DEEPLY and structurally (the
explicit post-patch composition / filter list), and SPEC_GUIDE §3 forbids
axiomatizing a deeply-modeled changed decision. The R legs are validated by
G-CONF. There is therefore no callee contract to validate against the real repo.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "sphinx-doc__sphinx-10323",
    "reason": "no consumed callee axiom; the selection and de-indentation callees "
              "are A-references identical in spec and impl (validated by G-CONF)",
}))
sys.exit(0)
