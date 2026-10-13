#!/usr/bin/env python3
"""G-AX — skip stub.

The proof consumes NO callee axiom: the axioms region of Solution.lean is empty.
The post-patch modeled branch of `_encode_params` (`return data`) calls nothing —
it is the identity on the payload. The removed coercion (`to_native_string`) is
modeled deeply only in the pre-patch impl (to exhibit the bug) and is not a
consumed axiom. There is therefore nothing for G-AX to validate against a real
callee.

stdlib-only. Emits status=skip and exits 0.
"""
import sys


def main() -> int:
    print("G-AX SKIP: no consumed callee axioms (axioms region empty); "
          "the modeled post-patch branch is the identity (I), no callee invoked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
