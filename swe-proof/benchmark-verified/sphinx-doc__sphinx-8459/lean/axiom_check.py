#!/usr/bin/env python
"""G-AX skip stub for sphinx-doc__sphinx-8459.

No consumed callee axiom is declared in the bundle. The modeled function is the
annotation-table recording in `record_typehints`. The one behaviour the gold
patch governs — resolving each annotation label against the configured
`autodoc_type_aliases` table before falling back to the default rendering — is
modeled DEEPLY in Lean (`renderName` = alias lookup with default fallback, an
A-reference) and validated by the differential `conformance_check.py` (G-CONF).
The default annotation renderer (`typing.stringify`, unchanged by the fix) is the
modeled function's free input `render`, quantified universally in the theorem —
not an axiomatized callee.

There is therefore nothing for G-AX to validate. Exit 0 with status=skip.
"""
import sys

if __name__ == "__main__":
    print("status=skip no consumed callee axioms (alias resolution modeled "
          "deeply; validated by G-CONF as an A-reference row)")
    sys.exit(0)
