#!/usr/bin/env python
"""G-AX skip stub for sympy__sympy-16766.

No consumed callee axiom is declared in the bundle. The new `_print_Indexed`
method invokes only UNCHANGED callees (`str(base)` and the recursive
`self._print(ind)`); their outputs enter the Lean model as the inputs `base`
and `subscripts`. The single operation the patch introduces is the string
assembly itself, which is modeled DEEPLY (literal concatenation + comma-join)
and validated by the differential `conformance_check.py` (G-CONF).

There is therefore nothing for G-AX to validate. Exit 0 with status=skip.
"""
import sys

if __name__ == "__main__":
    print("status=skip no consumed callee axioms (string assembly modeled "
          "deeply; validated by G-CONF as an A-reference)")
    sys.exit(0)
