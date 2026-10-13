#!/usr/bin/env python3
"""G-AX for pydata__xarray-3151 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference: the
decision the patch changes — which dimensions of the combined object are
subjected to the monotonicity requirement — is modeled DEEPLY and structurally
over the per-dimension observations (`isCoordDim`, `variesBetweenInputs`,
`isMonotonic`). The unchanged upstream callees (`is_monotonic_increasing` /
`is_monotonic_decreasing` on the pandas index, and `_infer_concat_order_from_coords`
which produces `concat_dims`) are orthogonal to the fix and enter the model as
those grounded observations rather than as axiomatized contracts. SPEC_GUIDE §3
forbids axiomatizing a deeply-modeled changed decision, so there is no callee
contract to validate against the real repo. The R legs are validated by G-CONF.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "pydata__xarray-3151",
    "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
              "(validated by G-CONF)",
}))
sys.exit(0)
