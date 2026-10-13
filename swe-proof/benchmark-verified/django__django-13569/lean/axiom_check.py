#!/usr/bin/env python3
"""G-AX skip stub for django__django-13569.

No consumed callee axiom is declared in the bundle. The behavior the patch
changes — a non-deterministic ordering term (`Random`) contributing no grouping
columns to an aggregated result set — is modeled DEEPLY in Lean as returning the
empty list (an R/I impl), validated against the real post-patch method by the
differential `conformance_check.py` (G-CONF), not by an axiom. The added method
`Random.get_group_by_cols` is a leaf that calls nothing and returns a constant
`[]`; there is no `opaque`/`axiom` callee whose contract the proof consumes.

There is therefore nothing for G-AX to validate. Exit 0 with status=skip.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "django__django-13569",
    "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
              "(constant empty grouping-column contribution validated by G-CONF)",
}))
sys.exit(0)
