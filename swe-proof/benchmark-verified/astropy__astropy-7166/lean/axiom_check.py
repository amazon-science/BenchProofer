#!/usr/bin/env python
"""G-AX skip stub for astropy__astropy-7166.

No consumed callee axiom is declared in the bundle. The only operation the patch
changes — the eligibility guard deciding which class members get a missing
documentation string filled (broadened to admit attribute-access descriptors,
not just ordinary callables) — is modeled DEEPLY in Lean (`eligible`, the boolean
predicate spelled out in `problem_spec_inheritDocstrings` /
`implementation_inheritDocstrings`, an A-reference). The unchanged base-class
resolution is folded into the `superDoc` input function (also an A-reference).
Both are validated against the real metaclass by the differential
`conformance_check.py` (G-CONF), not by an axiom.

There is therefore nothing for G-AX to validate. Exit 0 with status=skip.
"""
import sys

if __name__ == "__main__":
    print("status=skip no consumed callee axioms (eligibility guard and "
          "base-class resolution modeled deeply; validated by G-CONF as "
          "A-references)")
    sys.exit(0)
