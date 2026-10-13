#!/usr/bin/env python
"""G-AX skip stub for sympy__sympy-13877.

No consumed callee axiom is declared in the bundle. The zero test that decides
whether a column entry may serve as a pivot is modeled DEEPLY in Lean (the
`eval` / `isMathZero` helpers — an A-reference): an integer-polynomial
expression is mathematically zero exactly when it expands to the zero
polynomial. That model is validated against the real patched routine
(`_find_reasonable_pivot` with `_is_zero_after_expand_mul`) by the differential
`conformance_check.py` (G-CONF), not by an axiom. The operation the patch
changes — replacing literal-zero truthiness with a real zero test in pivot
selection — is captured structurally (the pre-patch impl uses the literal-zero
test and selects a mathematically-zero pivot).

There is therefore nothing for G-AX to validate. Exit 0 with status=skip.
"""
import sys

if __name__ == "__main__":
    print("status=skip no consumed callee axioms (zero test modeled deeply; "
          "validated by G-CONF as an A-reference)")
    sys.exit(0)
