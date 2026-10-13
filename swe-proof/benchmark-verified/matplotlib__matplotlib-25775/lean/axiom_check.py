#!/usr/bin/env python3
"""G-AX for matplotlib__matplotlib-25775 — skip stub.

The specification consumes no callee axiom: the antialiasing resolution is
modeled structurally over its three inputs (global default, optional ctor
value, optional later-set value). There is no `opaque`/`axiom` callee contract
to validate, so this gate is a no-op skip.
"""
import json
import sys

print(json.dumps({"status": "skip",
                  "reason": "no consumed callee axioms; resolution is structural"}))
sys.exit(0)
