#!/usr/bin/env python
"""G-AX skip stub for pytest-dev__pytest-10356.

No consumed callee axiom is declared in the bundle. The operation the patch
changes — gathering each class's own stored labels across the whole resolution
chain (instead of only the single resolved attribute) — is modeled DEEPLY in
Lean (the per-class flattening + concatenation spelled out in
`implementation_inheritedMarks` / `problem_spec_inheritedMarks`, an A-reference)
and validated against the real callee `get_unpacked_marks` by the differential
`conformance_check.py` (G-CONF), not by an axiom.

The only auxiliary step (`normalize_mark_list`, which coerces each stored entry
into Mark objects) is an order-preserving identity on values that are already
Mark objects, reproduced concretely by `flattenClassMarks`; it is not consumed
as an axiom property either.

There is therefore nothing for G-AX to validate. Exit 0 with status=skip.
"""
import sys

if __name__ == "__main__":
    print("status=skip no consumed callee axioms (MRO label gathering modeled "
          "deeply; validated by G-CONF as an A-reference)")
    sys.exit(0)
