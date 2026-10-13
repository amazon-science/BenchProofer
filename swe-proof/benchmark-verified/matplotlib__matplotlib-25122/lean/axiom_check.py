#!/usr/bin/env python3
"""G-AX for matplotlib__matplotlib-25122 — SKIP STUB.

The specification consumes no unchanged-callee axiom: the modeled behaviour is
the pure computation of the window-correction divisor from the window samples (a
signed sum, a sum of squares, or a squared signed sum), modeled deeply as
`for`-loop folds over `List Rat`. There is no `opaque`/`axiom _prop` callee
contract for the proof to consume, so G-AX has nothing to validate.

stdlib-only; exits 0 with status=skip.
"""
import json
import sys

print(json.dumps({"gate": "G-AX", "status": "skip",
                  "reason": "no consumed callee axioms; divisor is a pure "
                            "reduction over the window samples"}))
sys.exit(0)
