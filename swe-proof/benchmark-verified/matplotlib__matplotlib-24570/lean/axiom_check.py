#!/usr/bin/env python3
"""G-AX — skip stub.

This bundle consumes NO callee axiom: the axioms region of Solution.lean is empty
and the proof discharges the spec (a per-branch tuple equality) by case analysis
on `align`. There is also no A-reference deep model to validate — the only callee
(`max(... for ... in hd_list)`, baseline branch) is reproduced concretely as the
`maxList` fold (refinement.md row 3), an I op, not abstracted behind a model.

Therefore there is nothing for G-AX to check. Exit with the skip sentinel.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "reason": "no consumed axiom and no A-reference deep model "
                  "(axioms region empty; the max-reduction is reproduced "
                  "concretely as an I op)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
