#!/usr/bin/env python3
r"""G-AX — skip stub.

This bundle consumes NO callee axiom: the axioms region of Solution.lean is empty
and the proof discharges the spec (the content-type selection vs the
`finalContentType` predicate) directly. There is also no A-reference deep model
to validate — the changed op is the override dict's key set, reproduced
concretely as R/I-tagged ops (refinement.md), and `mimetypes.guess_type` is an
unchanged INPUT-boundary callee that merely supplies the two arguments (not
consumed inside the modeled computation).

Therefore there is nothing for G-AX to check. Exit with the skip sentinel.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "reason": "no consumed axiom and no A-reference deep model "
                  "(axioms region empty; the content-type override dict is "
                  "reproduced concretely as R/I ops; mimetypes.guess_type is an "
                  "unchanged input-boundary callee, not modeled)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
