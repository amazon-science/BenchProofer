#!/usr/bin/env python3
"""G-AX for pytest-dev__pytest-7236 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference: the
teardown-postponement decision (`teardownDeferralRule`) is modeled DEEPLY as a
pure Boolean function of three observables of the test case (async-path,
debugger-option-active, marked-to-skip), each of which enters as plain `Bool`
data. SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled changed decision, so
there is no callee contract to validate against the real repo. The R/I legs are
validated by G-CONF (exhaustive over the 8-point input space plus seeded fuzz).
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "pytest-dev__pytest-7236",
    "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
              "(validated by G-CONF)",
}))
sys.exit(0)
