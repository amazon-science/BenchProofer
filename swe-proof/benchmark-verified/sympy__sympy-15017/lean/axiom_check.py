#!/usr/bin/env python
"""G-AX skip stub for sympy__sympy-15017.

No consumed callee axiom is declared in the bundle. The modeled computation is
the element count of an N-dimensional array: the product of its shape's
dimension sizes. The single operation involved is integer multiplication folded
over the dimension list, which is modeled DEEPLY (a multiply accumulator seeded
at 1, i.e. List.prod) and validated by the differential `conformance_check.py`
(G-CONF) as an A-reference. There is no unchanged repo callee whose contract the
proof must assume.

There is therefore nothing for G-AX to validate. Exit 0 with status=skip.
"""
import sys

if __name__ == "__main__":
    print("status=skip no consumed callee axioms (element count modeled deeply "
          "as a product; validated by G-CONF as an A-reference)")
    sys.exit(0)
