#!/usr/bin/env python3
"""G-AX — axiom soundness check for sphinx-doc__sphinx-8548.

This bundle consumes NO `axiom <callee>_prop` and declares NO `opaque` callee:
the patch changes a control-flow STRUCTURE (it runs the comment-docstring
attribute-collection pass once per class in the inheritance chain instead of once
for the target class only) and the per-class match predicate (`ns == qualname`),
not a pure callee. The inheritance chain and the per-class recorded attribute
docstrings are INPUTS to the modeled function (`mro`, `ClassInfo.attrDocs`), and
the only deep model — the nested collection fold (`gatherMemberDocs` /
`addEntries`) — is a total recursion over the bijected `ClassInfo` chain, which is
validated by `conformance_check.py` (G-CONF) against an in-process replica of the
post-patch loop, rather than by sampling a real callee.

There is therefore nothing for G-AX to validate against a live callee, and this
script is a SKIP stub (SPEC_GUIDE: axiom_check.py "may be a skip stub" when the
proof needs no callee axiom). stdlib-only; exit 0.
"""
import sys


def main() -> int:
    print("status=skip reason=no consumed axiom and no opaque callee; "
          "the changed attribute-collection control flow is modeled deeply and "
          "checked by G-CONF")
    return 0


if __name__ == "__main__":
    sys.exit(main())
