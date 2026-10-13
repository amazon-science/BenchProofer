#!/usr/bin/env python3
"""G-AX — django__django-13023.  SKIP STUB.

The specification consumes NO callee axiom (`axioms = []`,
`deep_model_references = []` of the A-consumed kind; see refinement.md /
mapping.md).  The decimal conversion is modeled DEEPLY (and validated against the
real `decimal.Decimal` by G-CONF, not by an axiom), and the float branch is
abstracted to a normal return.  There is therefore no axiom property to check
against a real callee.  Exit with status=skip.
"""
import sys

if __name__ == "__main__":
    print("status=skip")
    print("reason=no consumed callee axiom (decimal conversion modeled deeply; "
          "validated by G-CONF)")
    sys.exit(0)
