#!/usr/bin/env python
"""G-AX skip stub for sympy__sympy-15349.

No consumed callee axiom is declared in the bundle. The modeled function builds
every matrix entry from exact rational arithmetic in the four quaternion
components (and, in the 4x4 case, the supplied point coordinates). The scale
`s = 1/(a^2+b^2+c^2+d^2)` and all nine quadratic entries are modeled DEEPLY in
Lean over `Rat`, so there is no unchanged dependency callee whose property the
proof consumes. The deep arithmetic model is validated against the real patched
`Quaternion.to_rotation_matrix` by the differential `conformance_check.py`
(G-CONF).

There is therefore nothing for G-AX to validate. Exit 0 with status=skip.
"""
import sys

if __name__ == "__main__":
    print("status=skip no consumed callee axioms (matrix entries modeled "
          "directly over Rat; validated by G-CONF as R/I ops)")
    sys.exit(0)
