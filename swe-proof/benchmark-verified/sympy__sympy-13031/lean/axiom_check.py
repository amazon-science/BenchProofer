#!/usr/bin/env python
"""G-AX skip stub for sympy__sympy-13031.

No consumed callee axiom is declared in the bundle. Both modeled functions (the
horizontal join `row_join` and the vertical join `col_join`) are modeled DEEPLY:
every output entry is a direct read of one input matrix's accessor at an index
computed purely from the inputs (`concatCols` / `concatRows`), and the empty
constructed receiver (`self._new(r, 0, [])` / `self._new(0, c, [])`) is modeled
as the identically-zero `zeroColsMat` / `zeroRowsMat`. None of these are callees
the patch leaves unchanged-but-relied-upon; the patched control flow + arithmetic
are R/I ops validated against the real patched primitives by the differential
`conformance_check.py` (G-CONF).

There is therefore nothing for G-AX to validate. Exit 0 with status=skip.
"""
import sys

if __name__ == "__main__":
    print("status=skip no consumed callee axioms (joins modeled directly; "
          "validated by G-CONF as R/I ops)")
    sys.exit(0)
