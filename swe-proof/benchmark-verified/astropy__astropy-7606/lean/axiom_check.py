#!/usr/bin/env python3
"""G-AX for astropy__astropy-7606 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference: the
behaviour the patch changes — whether an operand that cannot be interpreted as a
unit yields the not-applicable (NotImplemented) sentinel or lets the
interpretation failure escape — is modeled DEEPLY/structurally over `ParseOutcome`
(`.raised` -> `.notApplicable` vs propagation). The unchanged factory
`Unit(_, parse_strict='silent')` enters only as the grounded observation `po`,
whose value G-CONF computes by calling the REAL factory in-container. SPEC_GUIDE
§3 forbids axiomatizing a deeply-modeled changed decision, so there is no callee
contract to validate. The R legs are validated by G-CONF.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "astropy__astropy-7606",
    "reason": "no consumed callee axiom and no A-reference; impl is all R "
              "(validated by G-CONF, which drives the real Unit factory)",
}))
sys.exit(0)
