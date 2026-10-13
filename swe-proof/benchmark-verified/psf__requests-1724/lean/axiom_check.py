#!/usr/bin/env python
"""G-AX: axiom soundness for psf__requests-1724.

This bundle consumes NO `axiom <callee>_prop`: both modeled operations -- the
native coercion the patch adds (`builtin_str`) and the unchanged upper-casing
(`str.upper`) -- are modeled DEEPLY in Lean (clearing the wide flag and
`List.map Char.toUpper`), not axiomatized. There is therefore no callee contract
to validate here; their behavior is exercised end-to-end by conformance_check.py
(G-CONF).

Exit 0 with status=skip.
"""
import sys


def main():
    print("status=skip no callee axioms declared "
          "(native coercion + upper-casing modeled deeply, "
          "validated end-to-end by G-CONF)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
