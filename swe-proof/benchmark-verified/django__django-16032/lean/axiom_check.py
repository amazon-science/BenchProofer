#!/usr/bin/env python3
"""G-AX for django__django-16032.

`correct_prepInLookup` consumes NO `_prop` axiom. The modeled decision narrows
the right-hand-side subquery to the single target column directly (modeled as
the literal one-element selection `[targetField]`); the branch condition is the
explicit `has_select_fields` flag, which is part of the modeled state, not an
axiomatized callee. There is therefore no opaque callee whose property the proof
relies on for G-AX to validate.

The correspondence between the modeled decision and the real post-patch
`RelatedIn.get_prep_lookup` / `Query.has_select_fields` behavior is an R/I
concern, exercised mechanically by conformance_check.py (G-CONF). Hence this gate
is a principled skip stub.

stdlib-only; exit 0.
"""
import json
import sys

report = {
    "status": "skip",
    "instance": "django__django-16032",
    "reason": (
        "no consumed callee axiom: correct_prepInLookup proves the narrowing "
        "decision purely from the modeled SubqueryState (the explicit "
        "values-applied flag) and a literal one-element selection; there is no "
        "opaque callee property to validate. The decision's correspondence to "
        "the real post-patch RelatedIn.get_prep_lookup / Query.has_select_fields "
        "behavior is validated by conformance_check.py (G-CONF), not a _prop axiom."
    ),
    "axioms": [],
}
print(json.dumps(report, indent=2))
sys.exit(0)
