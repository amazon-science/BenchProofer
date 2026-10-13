#!/usr/bin/env python
"""G-AX skip stub for pydata__xarray-3095.

No consumed callee axiom is declared in the bundle. The only operation the patch
changes — preserving the index wrapper's stored element type (`dtype`) across a
copy instead of re-deriving it from the underlying sequence — is modeled DEEPLY
in Lean (`implementation_copy` / `problem_spec_copy`, an A-reference) and
validated against the real patched callee by the differential
`conformance_check.py` (G-CONF), not by an axiom.

There is therefore nothing for G-AX to validate. Exit 0 with status=skip.
"""
import sys

if __name__ == "__main__":
    print("status=skip no consumed callee axioms (stored-dtype preservation "
          "modeled deeply; validated by G-CONF as an A-reference)")
    sys.exit(0)
