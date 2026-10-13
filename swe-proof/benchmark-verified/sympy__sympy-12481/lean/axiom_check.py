#!/usr/bin/env python
"""G-AX skip stub for sympy__sympy-12481.

No consumed callee axiom is declared in the bundle. The cycle composition the
constructor performs (`Cycle.__call__` left-to-right product, then
`Cycle.list()`) is modeled DEEPLY in Lean (the `applyCycle` / `applyAll` /
`permSize` helpers — an A-reference) and validated against the real routine by
the differential `conformance_check.py` (G-CONF), not by an axiom. The operation
the patch changes — dropping the duplicate-element rejection for cyclic input —
is captured structurally (pre-patch impl returns `none`, post-patch `some`).

There is therefore nothing for G-AX to validate. Exit 0 with status=skip.
"""
import sys

if __name__ == "__main__":
    print("status=skip no consumed callee axioms (cycle composition modeled "
          "deeply; validated by G-CONF as an A-reference)")
    sys.exit(0)
