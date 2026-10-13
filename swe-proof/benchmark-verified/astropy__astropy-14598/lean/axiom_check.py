#!/usr/bin/env python3
"""G-AX — astropy__astropy-14598.

The bundle consumes NO callee axiom: the only operation under change is the
record-segment regex match, which is modeled DEEPLY (an A-reference validated by
conformance_check.py, not an axiomatized callee), and the surrounding string
primitives (rstrip / trailing-marker trim) are modeled deeply too. There is thus
no `axiom <callee>_prop` to validate against a real callee.

Exit 0 with status=skip.
"""
import sys

print("status=skip reason=no-consumed-axiom (regex modeled deeply as A-reference)")
sys.exit(0)
