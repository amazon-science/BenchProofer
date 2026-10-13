#!/usr/bin/env python3
"""G-AX — skip stub.

This bundle consumes NO callee axiom: the axioms region declares `opaque
combineEnv` (the unchanged ambient-overlay, `{**os.environ, **env}`) only so it
can appear in the executable impl and the frame clause, but NO `combineEnv_prop`
axiom is asserted and neither proof consumes any property of it. The fix's
discriminator is the empty/absent -> absent normalization, which is independent
of the overlay's contents.

`combineEnv` is tagged A-reference (refinement.md): its agreement with the real
`{**os.environ, **env}` dict spread is exercised by G-CONF (conformance_check.py
uses the real merge in its shadow), not by a G-AX axiom-property check.

Therefore there is nothing for G-AX to check. Exit with the skip sentinel.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "reason": "no consumed axiom (axioms region declares opaque combineEnv "
                  "with no _prop assertion); the A-reference overlay is validated "
                  "by G-CONF using the real dict merge, not by a G-AX property.",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
