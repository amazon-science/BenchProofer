#!/usr/bin/env python3
"""G-AX for sympy__sympy-24066 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference. The
`Function` branch of `UnitSystem._collect_factor_and_dimension` is modeled DEEPLY
over the observable it operates on — the per-argument (scale_factor, dimension)
pairs `fds`, produced by the (unchanged) recursive collection and carried as
plain data. SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled changed decision,
and §0.7 forbids axiomatizing the function under spec.

The two UNCHANGED callees the bundle touches — the dimensionless query and the
function reconstruction — are declared as opaque SIGNATURES only (`isDimensionless`,
`applyFunc`); NO `_prop` axiom asserts any property of them. They appear
identically in the spec and the impl, so they cancel in the differential test and
the proof consumes nothing about them. There is therefore no callee contract to
validate against the real repo. The R legs are validated by G-CONF.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "sympy__sympy-24066",
    "reason": "no consumed callee axiom and no A-reference; opaque callees are "
              "signature-only and cancel in the differential; impl R legs "
              "validated by G-CONF",
}))
sys.exit(0)
