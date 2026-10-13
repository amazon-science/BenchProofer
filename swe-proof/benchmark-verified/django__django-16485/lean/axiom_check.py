#!/usr/bin/env python3
"""G-AX — axiom soundness check for django__django-16485.

SKIP STUB. The bundle consumes NO callee `_prop` axiom: the opaque callees
(`decIsWhole`, `decIntPart`, `decimalDigits`, `numberFormat`) appear identically
in `problem_spec_floatformat` and `implementation_floatformat`, so they cancel in
the proof and no property of them is asserted or consumed (refinement.md tags
them R, not A-consumed/A-reference). There is therefore nothing to validate
against the real callees. Exit with status=skip.
"""
import sys

print("status=skip note=no consumed callee axiom (opaque callees cancel in proof)")
sys.exit(0)
