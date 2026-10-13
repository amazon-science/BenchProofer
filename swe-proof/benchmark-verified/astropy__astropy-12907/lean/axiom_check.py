#!/usr/bin/env python3
"""G-AX for astropy__astropy-12907 — SKIP STUB.

The combinator is modeled deeply (block-diagonal placement spelled out
element-wise); no unchanged callee's behavior is axiomatized. There are no
`axiom <callee>_prop` declarations in Solution.lean, so there is nothing for
G-AX to validate. Exit 0 with status=skip. stdlib-only.
"""
import json
import sys

print(json.dumps({"status": "skip", "reason": "no consumed axioms in bundle"}))
sys.exit(0)
