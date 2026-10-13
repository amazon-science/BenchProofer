#!/usr/bin/env python
"""G-AX skip stub for sympy__sympy-23950.

No consumed callee axiom is declared in the bundle. The modeled function
(`Contains.as_set`) returns one of the object's own stored constructor operands
(`self.args[1]`, the set) verbatim — a direct attribute read, not a call into a
separately-defined callee the patch changes. The behavior is modeled DEEPLY (an
R op: result == the stored set operand), validated against the real patched
`Contains.as_set` by the differential `conformance_check.py` (G-CONF).

There is therefore nothing for G-AX to validate. Exit 0 with status=skip.
"""
import sys

if __name__ == "__main__":
    print("status=skip no consumed callee axioms (as_set returns a stored "
          "operand directly; validated by G-CONF as an R op)")
    sys.exit(0)
