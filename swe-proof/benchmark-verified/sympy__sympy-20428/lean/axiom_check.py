#!/usr/bin/env python
"""G-AX skip stub for sympy__sympy-20428.

No consumed callee axiom is declared in the bundle. The only operation the patch
changes is the zero-test itself (`f.ex != 0` -> `not f.ex.is_zero`), which is
modeled DEEPLY by the two input flags (`isLiteralZero`, `isMathZero`) and
validated against the REAL patched `Expression.__bool__` by the differential
`conformance_check.py` (G-CONF) as an A-reference. Per SPEC_GUIDE §0.7 we do NOT
axiomatize the operation the patch changes.

There is therefore nothing for G-AX to validate. Exit 0 with status=skip.
"""
import sys

if __name__ == "__main__":
    print("status=skip no consumed callee axioms (zero-test modeled deeply; "
          "validated by G-CONF as an A-reference)")
    sys.exit(0)
