#!/usr/bin/env python3
"""G-AX — skip stub.

The proof consumes NO callee axiom: the axioms region of Solution.lean is empty.
The only computed value (`max_length or 254`) and the attribute assignment are
modeled deeply/concretely (R/I in refinement.md), not via an opaque callee with a
`_prop` axiom. There is therefore nothing for G-AX to validate against a real
callee.

stdlib-only. Emits status=skip and exits 0.
"""
import sys


def main() -> int:
    print("G-AX SKIP: no consumed callee axioms (axioms region empty); "
          "all ops modeled deeply/concretely (R/I)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
