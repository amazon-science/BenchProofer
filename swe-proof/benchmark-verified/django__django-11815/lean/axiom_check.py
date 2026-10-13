#!/usr/bin/env python3
"""G-AX — skip stub.

This bundle consumes NO callee axiom: the axioms region of Solution.lean is empty
and the proof discharges the spec (a concrete concatenation) directly. There is
also no A-reference deep model to validate — the only callee that appeared in the
modeled function (`serializer_factory(self.value.value).serialize()`, which
rendered the member payload) is DELETED by the patch, and the post-patch
rendering substitutes the module path, type name, and member identifier into the
literal template `'%s.%s[%r]'`, reproduced concretely as an I-tagged op
(refinement.md row 4), not abstracted behind a model.

Therefore there is nothing for G-AX to check. Exit with the skip sentinel.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "reason": "no consumed axiom and no A-reference deep model "
                  "(axioms region empty; the only callee is deleted by the "
                  "patch; literal-template substitution is reproduced "
                  "concretely as an I op)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
