#!/usr/bin/env python3
"""G-AX for scikit-learn__scikit-learn-13142.

The proof consumes NO callee `_prop` axiom: `labelsOf` is declared
`opaque`-signature-only (A-reference). The bug and fix concern WHICH parameter
configuration the final label computation is applied to (an ordering fact about
the selection fold), not any property of the label computation itself. There is
therefore no axiom to validate against the real callee — this is a skip stub.

stdlib-only; exit 0.
"""
import sys

print("status=skip reason=no consumed axiom (labelsOf is A-reference, signature only)")
sys.exit(0)
