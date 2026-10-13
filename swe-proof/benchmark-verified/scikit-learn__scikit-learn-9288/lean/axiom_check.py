#!/usr/bin/env python
"""G-AX skip stub for scikit-learn__scikit-learn-9288.

No consumed callee axiom is declared in the bundle. The only unchanged callee the
modeled function invokes is the per-attempt routine (`kmeans_single`), declared in
Lean as `opaque runTrial : Int -> Outcome`. The proof of `correct_bestTrial`
consumes NO property of it: the earliest-minimum-cost selection is correct for any
attempt routine whatsoever. There is therefore no `runTrial_prop` axiom to
validate.

The operation the patch changes — running the serial best-of-n_init loop over the
precomputed seed list (so each attempt is driven by the corresponding supplied
value) — is modeled DEEPLY in Lean (the selection loop spelled out in
`implementation_bestTrial` / `problem_spec_bestTrial`, an A-reference) and
validated against the real selection idioms by the differential
`conformance_check.py` (G-CONF), not by an axiom.

Exit 0 with status=skip.
"""
import sys

if __name__ == "__main__":
    print("status=skip no consumed callee axioms (per-attempt routine left opaque "
          "with no consumed property; selection modeled deeply and validated by "
          "G-CONF as an A-reference)")
    sys.exit(0)
