#!/usr/bin/env python
"""G-AX skip stub for django__django-12155.

No consumed callee axiom is declared in the bundle. The patched code's behavior
is the indentation normalization itself, which is modeled DEEPLY in Lean
(`normalizeIndentSpec` and the `problem_spec_normalizeIndent` relation,
A-reference rows) and validated against the real standard-library cleaner by the
differential `conformance_check.py` (G-CONF), not by an axiom. Tab expansion and
the split-into-lines / rejoin operations happen at the model boundary and are
bridged by `conformance_check.py`.

There is therefore nothing for G-AX to validate. Exit 0 with status=skip.
"""
import sys

if __name__ == "__main__":
    print("status=skip no consumed callee axioms (indentation normalization "
          "modeled deeply; validated by G-CONF as A-reference)")
    sys.exit(0)
