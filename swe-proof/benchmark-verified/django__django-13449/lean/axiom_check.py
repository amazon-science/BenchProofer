#!/usr/bin/env python3
"""G-AX — skip stub.

This bundle consumes NO callee axiom: the axioms region of Solution.lean is empty
and the proof discharges the spec (a concrete branch over two concatenations)
directly. There is also no A-reference deep model to validate — both callees
(the window template substitution `'%(expression)s OVER (%(window)s)'` and the
numeric-cast wrapper `'CAST(%s AS NUMERIC)' % sql`) are reproduced concretely as
I-tagged ops (refinement.md rows 3-4), not abstracted behind a model.

Therefore there is nothing for G-AX to check. Exit with the skip sentinel.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "reason": "no consumed axiom and no A-reference deep model "
                  "(axioms region empty; window template substitution and the "
                  "numeric-cast wrapper are reproduced concretely as I ops)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
