#!/usr/bin/env python
"""G-AX skip stub for matplotlib__matplotlib-14623.

No consumed callee axiom is declared in the bundle. The modeled behavior — the
direction-restoring reassembly of the normalized endpoints — is spelled out
concretely in Lean (`implementation_setLim` / `problem_spec_setLim`: capture the
requested direction, then exchange the committed pair iff the request was
descending). It consumes NO property of either dependency callee
(`normalizeRange` / `clampToDomain`): their results pass through verbatim and
the postcondition pins behavior by exact equality to those pass-through values.

The two callees are therefore A-reference (left as the real repo callees in the
differential `conformance_check.py`, G-CONF), not consumed axioms. There is
nothing for G-AX to validate. Exit 0 with status=skip.
"""
import sys

if __name__ == "__main__":
    print("status=skip no consumed callee axioms (direction-restoring "
          "reassembly modeled deeply; callees validated by G-CONF as "
          "A-references)")
    sys.exit(0)
