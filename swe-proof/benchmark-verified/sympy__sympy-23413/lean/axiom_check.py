#!/usr/bin/env python3
"""G-AX for sympy__sympy-23413 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference. The
change to `_hermite_normal_form` is entirely in the OUTER row-processing loop's
control flow — which row indices are iterated and the `k == 0` early break — and
that control flow is modeled DEEPLY over the row indices (`rowsDesc` / `hnfFold`
/ the imperative loop). SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled
changed op, and §0.7 forbids axiomatizing the function under spec.

The two UNCHANGED operations the bundle touches — the per-row reduction and the
final column slice — are declared as opaque SIGNATURES only (`step`,
`sliceCols`); NO `_prop` axiom asserts any property of either. They appear
identically in the spec (`hnfFold`) and the impl (the loop body), so they cancel
in the differential test and the proof consumes nothing about them. There is
therefore no callee contract to validate against the real repo. The R/I legs
(the row-selection control flow) are validated by G-CONF.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "sympy__sympy-23413",
    "reason": "no consumed callee axiom and no A-reference; opaque callees "
              "(step, sliceCols) are signature-only and cancel in the "
              "differential; impl R/I legs validated by G-CONF",
}))
sys.exit(0)
