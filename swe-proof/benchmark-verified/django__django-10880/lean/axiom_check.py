#!/usr/bin/env python3
"""G-AX — skip stub.

This bundle consumes NO callee axiom: the axioms region of Solution.lean is empty
and the proof discharges the spec (a concrete concatenation) directly. There is
also no A-reference deep model to validate — the only callee
(`super().as_sql`'s substitution into the literal template
`'%(function)s(%(distinct)s%(expressions)s)'`) is reproduced concretely as an
I-tagged op (refinement.md row 4), not abstracted behind a model.

Therefore there is nothing for G-AX to check. Exit with the skip sentinel.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "reason": "no consumed axiom and no A-reference deep model "
                  "(axioms region empty; literal-template substitution is "
                  "reproduced concretely as an I op)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
