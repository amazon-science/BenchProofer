#!/usr/bin/env python3
"""G-AX for sphinx-doc__sphinx-7590 — skip stub.

The bundle consumes NO unchanged-callee axiom: the `proof` region of
`correct_literalId` needs no property of the opaque recognisers (`floatMatch`,
`floatSuffixMatch`, `binMatch`, `hexMatch`, `decMatch`, `octMatch`,
`intSuffixMatch`, `udlMatch`). Each appears IDENTICALLY in the specification and
the implementation, so they are A-references that cancel in the differential test
rather than consumed `axiom … _prop`. The soundness-critical behaviour the patch
changes — the control flow that folds a trailing identifier into a user-defined
literal when a base literal carries no standard suffix — is modeled DEEPLY and
structurally (the explicit `finishLiteral` recombination + the three `get_id`
mangling formulas), and SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled
changed decision. The R legs are validated by G-CONF. There is therefore no
callee contract to validate against the real repo.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "sphinx-doc__sphinx-7590",
    "reason": "no consumed callee axiom; the lexical recognisers are A-references "
              "identical in spec and impl (validated by G-CONF)",
}))
sys.exit(0)
