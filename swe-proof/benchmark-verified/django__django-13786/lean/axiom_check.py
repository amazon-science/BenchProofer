#!/usr/bin/env python
"""G-AX skip stub for django__django-13786.

No consumed callee axiom is declared in the bundle. The only operation the patch
changes — overlaying the overriding option set and then clearing any managed key
the override does not re-specify — is modeled DEEPLY in Lean (the
overlay-then-clear spelled out in `implementation_combineOptions` /
`problem_spec_combineOptions`, an A-reference) and validated against the real
callee (`CreateModel.reduce`'s `AlterModelOptions` branch) by the differential
`conformance_check.py` (G-CONF), not by an axiom.

There is therefore nothing for G-AX to validate. Exit 0 with status=skip.
"""
import sys

if __name__ == "__main__":
    print("status=skip no consumed callee axioms (overlay-then-clear modeled "
          "deeply; validated by G-CONF as an A-reference)")
    sys.exit(0)
