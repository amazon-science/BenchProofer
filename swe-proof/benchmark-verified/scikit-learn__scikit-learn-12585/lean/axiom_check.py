#!/usr/bin/env python3
"""G-AX skip stub for scikit-learn__scikit-learn-12585.

No consumed callee axiom is declared in the bundle and no deep-model A-reference
is axiomatized. The modeled function is `clone(estimator, safe=True)`
(`sklearn/base.py`). The behavior the patch changes is a single boolean routing
guard:

    not hasattr(estimator,'get_params')  ->  ... or isinstance(estimator, type)

modeled DEEPLY in Solution.lean as
`configUnusable isBlueprint exposesConfig = (!exposesConfig) || isBlueprint`
over the value's own observable flags (SPEC_GUIDE 3: a deeply-modeled changed
decision is never axiomatized). The only non-trivial callee, `copy.deepcopy`, is
reached only on the no-config branch under `safe=False`, where for the value
shapes that get there (immutable leaves and class objects) it is observationally
the identity; it is modeled as the structural no-op of that branch (an R/I op),
not as an axiom. There is no `opaque` callee and no `axiom <callee>_prop` in
Solution.lean, so there is nothing for G-AX to validate.

The R/I impl (and its binding to the real patched `clone` routing) is
differential-tested by conformance_check.py (G-CONF).

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "scikit-learn__scikit-learn-12585",
        "reason": "no consumed callee axiom and no axiomatized A-reference; the "
                  "patched routing guard is modeled deeply (configUnusable) and "
                  "copy.deepcopy is the identity no-op of the no-config branch, "
                  "so the impl is all R/I (validated by G-CONF against the real "
                  "patched clone routing)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
