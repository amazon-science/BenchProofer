#!/usr/bin/env python3
"""G-AX for matplotlib__matplotlib-20488 — skip stub.

The bundle consumes NO unchanged-callee axiom. The behaviour the patch changes —
the sign/zero guard on the range's lower bound and the clamp to a positive floor
when a logarithmic scale is in use — is modeled DEEPLY and structurally in
`problem_spec_boundedRange` (a direct conditional on the lower bound's ordering
against 0). SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled changed decision.

The only quantity read from an unchanged library routine is the positive floor
(`np.finfo(scaled_dtype).eps`); it is modeled as an explicit input whose only
consumed property (`0 < floor`) is carried as a hypothesis of
`correct_boundedRange`, not as an axiomatized callee. There is therefore no
`opaque` declaration, no `axiom … _prop`, and no callee contract to validate
against the real repo. The R legs are validated by G-CONF.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "matplotlib__matplotlib-20488",
    "reason": "no consumed callee axiom; the sign/zero clamp is modeled deeply "
              "and the positive floor is an explicit input (0 < floor carried as "
              "a hypothesis), validated by G-CONF",
}))
sys.exit(0)
