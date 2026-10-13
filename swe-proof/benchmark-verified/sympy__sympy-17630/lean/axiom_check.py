#!/usr/bin/env python
"""G-AX skip stub for sympy__sympy-17630.

No consumed callee axiom is declared in the bundle. The modeled function (the
canonicalizing sum of matrix-valued terms) is modeled DEEPLY: the
canonicalization the fix's result flows through — drop the additive-identity
terms, canonically order the surviving named terms — is spelled out as
`canonicalizeMatrixSum` over the term list, with no opaque callee left as a
consumed axiom. It is an A-reference validated against the REAL patched
constructor-postprocessor (`Add(*terms).doit()` over matrix-valued terms) by the
differential `conformance_check.py` (G-CONF), never axiomatized (SPEC_GUIDE
Sec.0.7 / Sec.3).

There is therefore nothing for G-AX to validate. Exit 0 with status=skip.
"""
import sys

if __name__ == "__main__":
    print("status=skip no consumed callee axioms (matrix-sum canonicalization "
          "modeled directly; validated by G-CONF as an A-reference)")
    sys.exit(0)
