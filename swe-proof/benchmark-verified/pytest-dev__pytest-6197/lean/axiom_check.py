#!/usr/bin/env python3
"""G-AX for pytest-dev__pytest-6197 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference. The
modeled `Package.collect` enumeration is transliterated DEEPLY as a pure
operation over per-path observables (boundary / is-file / resolved collectors)
and the import side-effect flag. The two callees the real generator uses —
`_collectfile(path)` (per-file resolution) and the boundary predicate — are
UNCHANGED and enter as plain input data (the `yields` list and the `boundary`
Boolean), not as axiomatized contracts. SPEC_GUIDE §3 forbids axiomatizing a
deeply-modeled changed op; there is no callee contract to validate against the
real repo. The R legs are validated by G-CONF (faithful post-patch replica vs the
impl transliteration over seeded fuzz).
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "pytest-dev__pytest-6197",
    "reason": "no consumed callee axiom and no A-reference; impl is all R "
              "(validated by G-CONF)",
}))
sys.exit(0)
