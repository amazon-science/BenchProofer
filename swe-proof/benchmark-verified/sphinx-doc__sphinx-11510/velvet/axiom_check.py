#!/usr/bin/env python3
"""G-AX soundness check for sphinx-doc__sphinx-11510 — NO-OP (no axioms).

This bundle declares no axioms and no deep-model references (refinement.md §C).
The one arbitrary element of the change — the consumer-registered `source-read`
text handler — is modeled as a universally-quantified function parameter
`transform : List Char -> List Char` about which `Solution.lean` assumes nothing.
That is strictly stronger than any axiom (the spec must hold for EVERY handler)
and there is no real callee whose contract could be over-claimed, so there is
nothing for G-AX to execute.

Exits 0 with status=skip. meta.json gates.G-AX.status = "skip".
"""
import sys

if __name__ == "__main__":
    print("G-AX skip: no axioms / no deep-model references in this bundle; "
          "the consumer transform is a universally-quantified parameter.")
    sys.exit(0)
