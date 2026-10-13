#!/usr/bin/env python3
"""G-AX — axiom soundness check for sphinx-doc__sphinx-8475.

This bundle consumes NO `axiom <callee>_prop` and declares NO `opaque` callee:
the patch changes a control-flow DECISION (which probe-exception types fall back
to a full request), not a pure callee. The two network outcomes are INPUTS to the
modeled function (`light`, `full`), and the only deep model — `retryWithFull`, the
retry decision — is a total function over the bijected `ReqOutcome` enum, which is
validated exhaustively by `conformance_check.py` (G-CONF) rather than by sampling
a real callee.

There is therefore nothing for G-AX to validate against a live callee, and this
script is a SKIP stub (SPEC_GUIDE: axiom_check.py "may be a skip stub" when the
proof needs no callee axiom). stdlib-only; exit 0.
"""
import sys


def main() -> int:
    print("status=skip reason=no consumed axiom and no opaque callee; "
          "the changed retry decision is modeled deeply and checked by G-CONF")
    return 0


if __name__ == "__main__":
    sys.exit(main())
