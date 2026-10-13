#!/usr/bin/env python3
"""G-AX for matplotlib__matplotlib-13989 — SKIP STUB.

The specification consumes no unchanged-callee axiom: the modeled behaviour is
the pure assembly of a small keyword mapping (Python dict literal / item
assignment). There is no `opaque`/`axiom _prop` callee contract to validate, so
G-AX has nothing to check.

stdlib-only; exits 0 with status=skip.
"""
import json
import sys

print(json.dumps({"gate": "G-AX", "status": "skip",
                  "reason": "no consumed callee axioms; behaviour is pure dict assembly"}))
sys.exit(0)
