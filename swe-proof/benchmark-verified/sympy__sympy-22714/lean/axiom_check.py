#!/usr/bin/env python
"""G-AX skip stub for sympy__sympy-22714.

No consumed callee axiom is declared in the bundle. The only operation the patch
changes — classifying a coordinate as imaginary via the three-valued
determined-non-zero test `im(a).is_zero is False` instead of the raw truthiness
`im(a)` — is modeled DEEPLY in Lean (the per-coordinate predicate
`c.isNumber && (c.imagPartDetZero == some false)` in
`implementation_imaginaryCheck` / `problem_spec_imaginaryCheck`, an A-reference)
and validated against the real guard by the differential `conformance_check.py`
(G-CONF), not by an axiom.

The unchanged callees `is_number`, `im`, `is_zero` are read as input
observations and bridged into the `Coord` record; the bundle never consumes a
property axiom about them.

There is therefore nothing for G-AX to validate. Exit 0 with status=skip.
"""
import sys

if __name__ == "__main__":
    print("status=skip no consumed callee axioms (imaginary classification "
          "modeled deeply; validated by G-CONF as an A-reference)")
    sys.exit(0)
