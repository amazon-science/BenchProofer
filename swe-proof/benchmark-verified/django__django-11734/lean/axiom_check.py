#!/usr/bin/env python3
"""G-AX skip stub for django__django-11734.

No consumed callee axiom is declared in the bundle and no deep-model A-reference
is used. The modeled function (the filter-expression rewrite at the head of
`Query.split_exclude`) is modeled DEEPLY: the three-way RHS-shape dispatch and
the nesting-level adjustment are spelled out with concrete Lean operations
(`reanchor` / `implementation_relocateFilterIntoSubquery`). The correctness proof
closes against that concrete definition and consumes NO `axiom <callee>_prop`,
so there is no callee-property contract for G-AX to validate.

The R/I impl is differential-tested by conformance_check.py (G-CONF), which
diffs the Python shadow against the REAL patched rewrite using genuine
`django.db.models.OuterRef` / `F` objects.

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "django__django-11734",
        "reason": "no consumed callee axiom and no A-reference; the split_exclude "
                  "RHS re-anchoring is modeled deeply (three-way shape dispatch + "
                  "level adjustment), proof closes against the concrete def; "
                  "behavior validated by G-CONF",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
