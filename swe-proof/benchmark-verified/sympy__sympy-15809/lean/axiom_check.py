#!/usr/bin/env python
"""G-AX: axiom soundness check for sympy__sympy-15809.

This bundle consumes NO callee `_prop` axioms and declares NO opaque callees:
the reduction over comparable extended reals is modeled deeply as a fold (an R
leg), so faithfulness is carried by G-CONF (conformance_check.py), not by an
axiom. There is therefore nothing to validate here.

Exit 0 (skip).
"""
import sys

print("status=skip no consumed axioms (reduction modeled deeply as a fold; "
      "checked by G-CONF)")
sys.exit(0)
