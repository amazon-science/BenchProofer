#!/usr/bin/env python
"""G-AX skip stub for matplotlib__matplotlib-25960.

No consumed callee axiom is declared in the bundle. The only nontrivial callee
the fix newly invokes (`GridSpec.get_grid_positions`, which turns the requested
spacing into per-cell grid positions) is modeled DEEPLY in Lean as the closed-form
`gridRects` / `panelExtent` / `panelGap` arithmetic (an A-reference), and is
validated against the real patched `Figure.subfigures` by the differential
`conformance_check.py` (G-CONF), not by an axiom. `Bbox.from_extents` and the
bbox-application step are identity ops (`Rect.ofExtents` / storing the rectangle).

There is therefore nothing for G-AX to validate. Exit 0 with status=skip.
"""
import sys

if __name__ == "__main__":
    print("status=skip no consumed callee axioms (grid positions modeled deeply "
          "as gridRects; validated by G-CONF as an A-reference)")
    sys.exit(0)
