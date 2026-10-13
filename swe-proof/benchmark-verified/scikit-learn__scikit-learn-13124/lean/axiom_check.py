#!/usr/bin/env python
"""G-AX skip stub for scikit-learn__scikit-learn-13124.

No consumed callee axiom is declared in the bundle. The random generator is taken
OPAQUELY (`seedState`, `shuffleN`) and the spec/proof assert NO property of it
(no `_prop` axiom). The only thing pinned is the THREADING discipline — seed one
generator, consume it once per class carrying the advanced state forward — which
holds for any generator by structure. The real generator's behaviour (that it
advances as it is consumed, so threading differs from re-seeding) is validated as
an A-reference by the differential `conformance_check.py` (G-CONF), which drives
the genuine repo `check_random_state` + `RandomState.shuffle`.

There is therefore nothing for G-AX to validate. Exit 0 with status=skip.
"""
import sys

if __name__ == "__main__":
    print("status=skip no consumed callee axioms (generator threading modeled "
          "deeply; the real generator is validated by G-CONF as an A-reference)")
    sys.exit(0)
