#!/usr/bin/env python
"""G-AX skip stub for matplotlib__matplotlib-24026.

No consumed callee axiom is declared in the bundle. The only operation the patch
introduces (cycling through the supplied palette: the i-th color is
`itertools.cycle(colors)`'s i-th yield = `colors[i % len(colors)]`) is modeled
DEEPLY in Lean as `nthColor` (an A-reference), and is validated against the real
patched `stackplot` by the differential `conformance_check.py` (G-CONF), not by
an axiom.

There is therefore nothing for G-AX to validate. Exit 0 with status=skip.
"""
import sys

if __name__ == "__main__":
    print("status=skip no consumed callee axioms (palette cycling modeled "
          "deeply as nthColor; validated by G-CONF as an A-reference)")
    sys.exit(0)
