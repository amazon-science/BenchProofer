#!/usr/bin/env python
"""G-AX skip stub for sympy__sympy-16792.

No consumed callee axiom is declared in the bundle: the only operation the patch
introduces (`dimensions(s) = [(S.Zero, dim-1) for dim in s.shape]`) is modeled
DEEPLY in Lean as `boundsOf` (an A-reference), and is validated against the real
callee by the differential `conformance_check.py` (G-CONF), not by an axiom.

There is therefore nothing for G-AX to validate. Exit 0 with status=skip.
"""
import sys

if __name__ == "__main__":
    print("status=skip no consumed callee axioms (dimensions modeled deeply; "
          "validated by G-CONF as an A-reference)")
    sys.exit(0)
