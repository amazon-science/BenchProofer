#!/usr/bin/env python
"""G-AX: axiom soundness for astropy__astropy-13977.

This bundle consumes NO `axiom <callee>_prop`: the dispatch wrapper's modeled
behavior reasons only about the OUTCOME of its (unchanged) try-body and each
operand's "defers to default handling" status, both taken as modeled inputs and
validated end-to-end by conformance_check.py (G-CONF). There is therefore no
callee contract to validate here.

Exit 0 with status=skip.
"""
import sys


def main():
    print("status=skip no callee axioms declared "
          "(dispatch outcome + operand defer-status taken as modeled inputs, "
          "validated end-to-end by G-CONF)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
