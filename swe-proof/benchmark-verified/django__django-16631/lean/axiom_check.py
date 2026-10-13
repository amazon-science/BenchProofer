#!/usr/bin/env python3
"""G-AX — skip stub.

This bundle consumes NO callee axiom: the axioms region of Solution.lean is empty
and the proof discharges the spec (a control-flow decision over the three token
inputs) directly. There is also no A-reference deep model to validate — the only
callee inside the modeled decision (`constant_time_compare`) is reproduced
concretely as list equality (refinement.md rows 4-5), an I-tagged op. The
token-producing callees (`get_session_auth_hash` / `get_session_auth_fallback_hash`)
supply the model's inputs and are not operations of the modeled function.

Therefore there is nothing for G-AX to check. Exit with the skip sentinel.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "reason": "no consumed axiom and no A-reference deep model "
                  "(axioms region empty; constant_time_compare is reproduced "
                  "concretely as list equality, an I op)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
