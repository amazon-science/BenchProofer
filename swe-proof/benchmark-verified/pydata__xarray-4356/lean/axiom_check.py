#!/usr/bin/env python3
"""G-AX for pydata__xarray-4356 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference: the
behavior the patch changes — the per-cell count of reduced entries (the product
of the reduced-axis sizes) and its comparison to the required minimum — is
modeled DEEPLY as pure functions (`reducedCellValue`, `enforceMinCount`,
`List.prod`, `Int` arithmetic) over the observable inputs (the reduced-axis
sizes, each cell's value and missing-element count, the minimum, the fill
sentinel). SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled changed op, so
there is no callee contract to validate against the real repo. The R legs are
validated by G-CONF.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "pydata__xarray-4356",
    "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
              "(validated by G-CONF)",
}))
sys.exit(0)
