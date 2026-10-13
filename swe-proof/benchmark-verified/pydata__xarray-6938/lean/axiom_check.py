#!/usr/bin/env python3
"""G-AX — skip stub.

This bundle consumes NO callee axiom: the axioms region of Solution.lean is
empty and the proof discharges the spec (freshness + heap growth + content +
frame of a fresh `Array.push`) directly from the array semantics.

There is also no A-reference deep model to validate against an isolated real
callee. The only callee the fix introduces — `IndexVariable.copy()` — is not
abstracted behind a model; its "structural duplicate that is a new object"
semantics ARE the modeled changed op (refinement.md rows 2-4), exercised
end-to-end by G-CONF (conformance_check.py) rather than in isolation.

Therefore there is nothing for G-AX to check. Exit with the skip sentinel.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "reason": "no consumed axiom and no A-reference deep model "
                  "(axioms region empty; the copy/freshness semantics are the "
                  "modeled changed op, checked end-to-end by G-CONF)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
