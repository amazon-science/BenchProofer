#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-17655.

SKIPPED — conf_skip=true (meta.json).

G-CONF mechanically refutes the R/I refinement legs of refinement.md by
differential-testing a Python shadow of the impl region's R/I ops against
patch.diff's behaviour. For this bundle the impl region of `scalePoint`
(Solution.lean) is a SINGLE A-tagged operation — the delegation
`let out :| out = scaleCoords coords factor`, where `scaleCoords` is the deep
model of the UNCHANGED point-by-scalar scaling callee (an A-reference, §3). There
are no R/I-tagged computed ops in the impl region (the type refinement of the
scalar/coordinate carrier is covered by mapping.md §2; the scaling itself is the
A-reference). Per the construction rules, an all-A-tagged impl region sets
`meta.json conf_skip=true` and ships this skip stub.

The soundness that G-CONF would otherwise provide is fully discharged here by
G-AX (`axiom_check.py`): it validates `scaleCoords` == the real UNCHANGED scaling
callee `Point.__mul__` on boundary + 20000 fuzz point/factor pairs. (The
left==right delegation is the patched behaviour, checked by G-RESOLVE.)

Exit status: status=skip (a non-failing, non-pass sentinel the orchestrator
recognizes for conf_skip bundles).
"""
import sys


def main():
    print("G-CONF SKIP: impl region of scalePoint is all-A-tagged (the single "
          "delegation to the deep-modeled scaling callee scaleCoords, an "
          "A-reference). No R/I computed ops to differential-test; soundness is "
          "covered by axiom_check.py (G-AX). status=skip")
    return 0


if __name__ == "__main__":
    sys.exit(main())
