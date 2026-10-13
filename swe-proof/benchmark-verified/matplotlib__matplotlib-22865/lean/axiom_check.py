#!/usr/bin/env python3
"""G-AX skip stub for matplotlib__matplotlib-22865.

No consumed callee axiom is declared in the bundle and no deep-model
A-reference op is used: the two end-openness settings (`_extend_lower()` /
`_extend_upper()`) enter the model as plain boolean inputs, and the segment
carrier (`np.dstack([X, Y])`) enters as the input list with an identity
bijection. The only operation performed is the index-and-slice selection,
modeled directly in Lean (`take`/`drop`). There is no `opaque` callee and no
`axiom <callee>_prop` in Solution.lean, so there is nothing for G-AX to
validate. The full R/I impl is differential-tested by conformance_check.py
(G-CONF).

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "matplotlib__matplotlib-22865",
        "reason": "no consumed callee axiom and no A-reference op; impl is all "
                  "R/I (validated by G-CONF)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
