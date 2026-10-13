#!/usr/bin/env python
"""G-AX skip stub for sympy__sympy-13647.

No consumed callee axiom is declared in the bundle. The modeled function is the
per-entry accessor of `col_insert`; each of its three branches is a direct read
of an input matrix's entry accessor at an index computed purely from the inputs
(`self[i, j]`, `other[i, j - pos]`, `self[i, j - other.cols]`). These accessors
are not callees the patch changes, and the patched arithmetic is modeled DEEPLY
(an R op), validated against the real patched `col_insert` by the differential
`conformance_check.py` (G-CONF).

There is therefore nothing for G-AX to validate. Exit 0 with status=skip.
"""
import sys

if __name__ == "__main__":
    print("status=skip no consumed callee axioms (entry accessor modeled "
          "directly; validated by G-CONF as R/I ops)")
    sys.exit(0)
