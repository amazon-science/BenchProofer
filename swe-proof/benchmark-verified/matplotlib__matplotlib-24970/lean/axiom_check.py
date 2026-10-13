#!/usr/bin/env python
"""G-AX skip stub for matplotlib__matplotlib-24970.

No consumed callee axiom is declared in the bundle. The only behavior the patch
governs — recording each integer data value's lookup-table row index exactly
(in-range values keep their own index; out-of-range values are sent to the
dedicated reserved `under` / `over` slots `N` / `N + 1`) regardless of the input
value type's capacity — is modeled DEEPLY in Lean (`desiredIndex` /
`implementation_index` / `problem_spec_index`, an A-reference) and validated
against the real callee `Colormap.__call__` by the differential
`conformance_check.py` (G-CONF), not by an axiom.

There is therefore nothing for G-AX to validate. Exit 0 with status=skip.
"""
import sys

if __name__ == "__main__":
    print("status=skip no consumed callee axioms (integer-index mapping modeled "
          "deeply; validated by G-CONF as an A-reference)")
    sys.exit(0)
