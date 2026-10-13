#!/usr/bin/env python3
"""G-AX — skip stub.

This bundle consumes NO callee axiom: the axioms region of Solution.lean is empty
and the proof discharges the spec (`result = written`) directly. There is also no
A-reference deep model to validate against a real callee — the readback
transformation is modeled concretely as R-tagged ops (refinement.md): the
post-patch readback is the identity copy, the pre-patch readback is universal
newline translation. `io.TextIOWrapper.read` is not abstracted behind a property
that the proof consumes.

Therefore there is nothing for G-AX to check. Exit with the skip sentinel.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "reason": "no consumed axiom and no A-reference deep model "
                  "(axioms region empty; the readback transformation is "
                  "reproduced concretely as R ops, not axiomatized)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
