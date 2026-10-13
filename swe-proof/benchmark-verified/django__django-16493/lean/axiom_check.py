#!/usr/bin/env python3
"""G-AX — skip stub.

This bundle consumes NO callee axiom: the axioms region of Solution.lean is empty
and the proof discharges the spec (an `Option.getD` then an `if` on `Nat`
equality) directly. There is also no A-reference deep model to validate — the
only callees touched (`getattr`-with-default and the `is not default_storage`
identity test) are reproduced concretely as R ops (`Option.getD` / `Nat`
inequality; refinement.md rows 4-5), not abstracted behind a model.

Therefore there is nothing for G-AX to check. Exit with the skip sentinel.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "reason": "no consumed axiom and no A-reference deep model "
                  "(axioms region empty; the original-reference fallback and the "
                  "identity comparison are reproduced concretely as R ops)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
