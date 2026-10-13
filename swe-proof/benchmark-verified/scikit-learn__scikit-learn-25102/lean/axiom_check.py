#!/usr/bin/env python3
"""G-AX — axiom soundness check for scikit-learn__scikit-learn-25102.

SKIP STUB. The bundle consumes no callee axiom and declares no `opaque` callee:
the changed operations (the preserve-or-homogenise decision under the
`isDataFrame && outputPandas` gate, and the by-flag column selection) are modeled
DEEPLY in `Solution.lean` as `castAll`/`selectByMask`, structural maps/filters
over the input columns and the selection vector. There is therefore no
`axiom <callee>_prop` whose property a real callee must satisfy, so there is
nothing for G-AX to validate.

stdlib-only; exits 0 with status=skip.
"""
import sys


def main() -> int:
    print("no consumed callee axiom / no opaque callee in bundle")
    print("status=skip")
    return 0


if __name__ == "__main__":
    sys.exit(main())
