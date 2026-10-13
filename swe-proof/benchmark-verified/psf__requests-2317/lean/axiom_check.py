#!/usr/bin/env python
"""G-AX: axiom soundness for psf__requests-2317.

This bundle consumes NO `axiom <callee>_prop`: both modeled operations — the
text-recovery the patch switches to (`to_native_string`) and the unchanged
upper-casing (`str.upper`) — are modeled DEEPLY in Lean (`nativeContent` and
`List.map Char.toUpper`), not axiomatized. There is therefore no callee contract
to validate here; their behavior is exercised end-to-end by conformance_check.py
(G-CONF).

Exit 0 with status=skip.
"""
import sys


def main():
    print("status=skip no callee axioms declared "
          "(text recovery + upper-casing modeled deeply, "
          "validated end-to-end by G-CONF)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
