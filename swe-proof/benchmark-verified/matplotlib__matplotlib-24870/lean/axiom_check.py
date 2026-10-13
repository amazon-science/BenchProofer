#!/usr/bin/env python
"""G-AX skip stub for matplotlib__matplotlib-24870.

No consumed callee axiom is declared in the bundle. The operation the patch
changes — selecting the contour level specification (an explicit mid-level /
bracketing-values set for boolean-valued data, versus the default automatic
count otherwise) — is modeled value-exactly in Lean
(`implementation_chooseLevels` / `problem_spec_chooseLevels`). The only callee
involved (the downstream routine that expands the default count into concrete
automatic levels) is UNCHANGED by the patch, runs only AFTER the modeled
decision, and is validated against the REAL routine by the differential
`conformance_check.py` (G-CONF) as an A-reference — not assumed as an axiom.

There is therefore nothing for G-AX to validate. Exit 0 with status=skip.
"""
import sys

if __name__ == "__main__":
    print("status=skip no consumed callee axioms (level selection modeled "
          "value-exactly; downstream count-expansion validated by G-CONF as an "
          "A-reference)")
    sys.exit(0)
