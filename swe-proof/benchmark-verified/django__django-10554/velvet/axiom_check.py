#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-10554.

This bundle has NO axiomatized callees and NO A-reference deep models of an
external callee (mapping.md §3, refinement.md §C). The only operation the gold
patch changes — the disposition of an ordering term in the no-match (`else`)
case of the combinator search loop in `get_order_by`, now split by
`bool(col_alias)` into rejected-vs-appended — is modeled DEEPLY and CONCRETELY
in Solution.lean (`firstAligned` / `lastLabelled` / `disposition` over the
`Candidate` / `Disposition` carriers). The surrounding per-candidate resolution
machinery is UNCHANGED by the patch and is abstracted to two structural booleans
(`aligns`, `labelled`); it is exercised by G-CONF (conformance_check.py), not
asserted as an axiom.

There is therefore nothing to validate against a real callee: G-AX is vacuous.
This script emits status=skip, as recorded in meta.json (axioms: [],
deep_model_references: [], G-AX.status="skip").
"""
import json
import sys


def main():
    result = {
        "instance": "django__django-10554",
        "status": "skip",
        "reason": ("no axioms and no A-reference deep models of an external "
                   "callee; the changed ordering-term disposition (rejected vs "
                   "appended, split on col_alias) is modeled deeply "
                   "(firstAligned/lastLabelled/disposition) and validated "
                   "structurally by G-CONF, not against a real callee"),
        "axioms_checked": 0,
        "deep_model_references_checked": 0,
    }
    print(json.dumps(result))
    print("G-AX SKIP: no callee axioms to validate (see mapping.md sec.3).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
