#!/usr/bin/env python3
"""G-AX — skip stub.

This bundle consumes NO callee axiom: the axioms region of Solution.lean is empty
and the proof discharges the spec (a two-field postcondition on the returned
object) directly by case analysis on the async-mode flag. There is also no
A-reference deep model to validate — the response constructor and the
permitted-methods list are unchanged inputs reproduced concretely as R/I-tagged
ops (refinement.md), not abstracted behind a model that needs validation.

Therefore there is nothing for G-AX to check. Exit with the skip sentinel.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "reason": "no consumed axiom and no A-reference deep model "
                  "(axioms region empty; the async-mode flag and permitted-"
                  "methods list are unchanged inputs reproduced as R/I ops)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
