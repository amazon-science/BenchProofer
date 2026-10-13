#!/usr/bin/env python
"""G-AX skip stub for pydata__xarray-6744.

No consumed callee axiom is declared in the bundle. The only operation the patch
changes — the per-position start/stop index arithmetic that decides which
contiguous slice each rolling window covers, gated on the alignment flag — is
modeled DEEPLY in Lean (`winOffset` / `winStart` / `windowAt` spelled out as
list `drop`/`take`, an R leg) and validated against the real patched iterator by
the differential `conformance_check.py` (G-CONF), not by an axiom.

There are no `opaque <callee>` declarations and no `axiom <callee>_prop` in
Solution.lean, so there is nothing for G-AX to validate. Exit 0 with
status=skip.
"""
import sys

if __name__ == "__main__":
    print("status=skip no consumed callee axioms (window start/stop arithmetic "
          "modeled deeply as list slices; validated by G-CONF)")
    sys.exit(0)
