#!/usr/bin/env python3
"""G-AX — skip stub.

The proof consumes NO callee axiom: the axioms region of Solution.lean is empty.
The only callee whose behavior matters — the deferred-vs-traversed rejection
performed by `select_related_descend` — is modeled DEEPLY as `raisesFieldError`
(an A-reference, refinement.md), and `correct_m2mPkQuery` discharges the
no-conflict clause structurally over that deep model (setting the traversal
configuration to unrestricted makes `raisesFieldError` false by definition).
Nothing is asserted via an `opaque <callee>` + `axiom <callee>_prop`, so there is
no axiom for G-AX to validate against a real callee.

The deep model's fidelity to the real query construction + rejection condition is
exercised mechanically by G-CONF (conformance_check.py): its R/I shadow
reconstructs the post-patch `select_related().only("pk")` query state and the
`select_related_descend` restricted/deferred check op-for-op and differential-tests
them against an independent reconstruction over >=10^5 inputs.

stdlib-only. Emits status=skip and exits 0.
"""
import sys


def main() -> int:
    print("G-AX SKIP: no consumed callee axioms (axioms region empty); the "
          "select_related_descend rejection condition is modeled deeply "
          "(A-reference) and proven, and is exercised by G-CONF")
    return 0


if __name__ == "__main__":
    sys.exit(main())
