#!/usr/bin/env python
"""G-AX skip stub for matplotlib__matplotlib-23412.

No consumed callee axiom is declared in the bundle. The only operation the patch
changes — handing the renderer the full configured dash pattern `(offset,
dashes)` instead of `(0, dashes)` during `draw` — is modeled DEEPLY in Lean (the
verbatim carry-through spelled out in `implementation_dashRender` /
`problem_spec_dashRender`, an A-reference) and validated against the real callee
(`matplotlib.patches.Patch.draw`) by the differential `conformance_check.py`
(G-CONF), not by an axiom.

There is therefore nothing for G-AX to validate. Exit 0 with status=skip.
"""
import sys

if __name__ == "__main__":
    print("status=skip no consumed callee axioms (in-draw dash-pattern "
          "carry-through modeled deeply; validated by G-CONF as an A-reference)")
    sys.exit(0)
