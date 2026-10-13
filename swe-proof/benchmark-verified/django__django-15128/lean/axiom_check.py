#!/usr/bin/env python3
"""G-AX — skip stub.

This bundle consumes NO callee axiom: the axioms region of Solution.lean is empty
and the proof discharges the spec (the change-map construction, a pure `filterMap`
over the indexed alias list) directly. There is also no A-reference deep model to
validate — the changed operation (the `if alias not in exclude` filter and the
positional `'%s%d' % (prefix, pos)` naming) is reproduced concretely as I/R-tagged
ops (refinement.md rows 2-4), not abstracted behind a callee model. The downstream
`change_aliases` that consumes the map is unchanged by the patch and is not part
of the modeled value.

Therefore there is nothing for G-AX to check. Exit with the skip sentinel.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "reason": "no consumed axiom and no A-reference deep model "
                  "(axioms region empty; the change-map construction is "
                  "modeled deeply as a filterMap over the indexed alias list)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
