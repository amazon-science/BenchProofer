#!/usr/bin/env python
"""G-AX skip stub for sphinx-doc__sphinx-8056.

No consumed callee axiom is declared in the bundle, and no `opaque` callee
signature is used. The two operations the patch introduces — separating a
parameter name on commas and trimming surrounding blanks from each piece — are
modeled DEEPLY in Lean (`commaPieces` / `trim`, A-references) and validated
against their real library counterparts (`str.split(",")` / `str.strip()`) by the
differential `conformance_check.py` (G-CONF). The unchanged entry-reading and
section-boundary bookkeeping are abstracted into the input list and not modeled.

There is therefore nothing for G-AX to validate. Exit 0 with status=skip.
"""
import sys

if __name__ == "__main__":
    print("status=skip no consumed callee axioms (comma-split and blank-trim "
          "modeled deeply; validated by G-CONF as A-references)")
    sys.exit(0)
