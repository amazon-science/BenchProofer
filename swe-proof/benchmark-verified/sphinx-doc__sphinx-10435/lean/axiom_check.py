#!/usr/bin/env python
"""G-AX skip stub for sphinx-doc__sphinx-10435.

No consumed callee axiom is declared in the bundle. The modeled function is the
highlighted-`code`-role post-processing in `LaTeXTranslator.visit_literal`; every
operation the patch changes (`str.replace` adding `%`, the `[:-14]`->`[:-15]`
trailer slice, and the `'}}'`->`'%'+CR+'}}'` closing string) is modeled DEEPLY in
Lean (`replaceAll` / `dropLastN` / `closingTail`, all A-reference) and validated
against the real string operations by the differential `conformance_check.py`
(G-CONF). The highlighter output `hlcode` is a free input of the theorem, not an
axiomatized callee.

There is therefore nothing for G-AX to validate. Exit 0 with status=skip.
"""
import sys

if __name__ == "__main__":
    print("status=skip no consumed callee axioms (post-processing modeled "
          "deeply; validated by G-CONF as A-reference rows)")
    sys.exit(0)
