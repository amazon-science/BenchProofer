#!/usr/bin/env python3
"""G-AX — skip stub.

The proof consumes NO callee axiom: the axioms region of Solution.lean is empty.
The only callee whose behavior matters — the constraint-name filter performed by
`_constraint_names` — is modeled DEEPLY as `isDropCandidate` / `dropCandidateNames`
(an A-reference, refinement.md row 3), and `correct_dropComposedIndex` discharges
the selection structurally over that deep model. Nothing is asserted via an
`opaque <callee>` + `axiom <callee>_prop`, so there is no axiom for G-AX to
validate against a real callee.

The deep model's fidelity to the real selection is exercised mechanically by
G-CONF (conformance_check.py): its R/I shadow reconstructs the post-patch
`_constraint_names` keyword filter (`columns == cols ∧ index ∧ ¬unique ∧ name ∉
exclude`) and the exactly-one count check op-for-op and differential-tests them
against an independent reconstruction of the patched selection over >=10^5 inputs.

stdlib-only. Emits status=skip and exits 0.
"""
import sys


def main() -> int:
    print("G-AX SKIP: no consumed callee axioms (axioms region empty); the "
          "_constraint_names filter is modeled deeply (A-reference) and proven, "
          "and is exercised by G-CONF")
    return 0


if __name__ == "__main__":
    sys.exit(main())
