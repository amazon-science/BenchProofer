#!/usr/bin/env python3
"""G-AX for astropy__astropy-14182 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference. Both
modeled behaviors — the index of the bracketing column-rule line when emitting,
and the data start-line position when parsing — are modeled DEEPLY as pure
functions of the number of header rows (`numHeaderRows`), with the rendered
sequence of lines entering the emit case as a direct input observation rather
than being recomputed. SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled
changed decision, so there is no callee contract to validate against the real
repo. The R/I legs are validated by G-CONF.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "astropy__astropy-14182",
    "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
              "(validated by G-CONF)",
}))
sys.exit(0)
