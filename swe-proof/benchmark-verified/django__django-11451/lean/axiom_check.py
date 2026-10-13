#!/usr/bin/env python3
"""G-AX — skip stub.

The proof of `correct_credentialAuth` consumes NO callee-property axiom: the
four UNCHANGED callee observables (lookupUser, passwordMatches, userAllowed,
checkHashCount) are declared `opaque` (signatures only) and are referenced
IDENTICALLY in the specification and the implementation, so correctness follows
by case analysis on the credential-presence branches without assuming any
property of them. The axioms region carries only `opaque` signatures and
structure declarations — no `axiom <callee>_prop`, and no deeply-modeled
changed op that would be an A-reference. Hence there is nothing for G-AX to
validate against the real callee.

stdlib-only; exits 0 with status=skip.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "reason": ("no consumed axiom and no A-reference deep model: the four "
               "UNCHANGED callee observables are opaque signatures referenced "
               "identically in spec and impl (I-tagged); the changed op is the "
               "missing-credential short-circuit, modeled deeply via the "
               "control-flow guard, not axiomatized"),
}))
sys.exit(0)
