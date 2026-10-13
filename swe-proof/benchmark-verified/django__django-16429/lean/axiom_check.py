#!/usr/bin/env python3
"""G-AX skip stub for django__django-16429.

No consumed callee axiom is declared in the bundle. The behavior the patch
changes — the pivot datetime construction now carrying the starting instant's
timezone designation onto the constructed reference instant — is modeled DEEPLY
in Lean as a field-by-field structure assembly over `d`'s fields plus the
constant month-length table and integer `min`/arithmetic (an R/I impl), validated
against the real post-patch construction by the differential `conformance_check.py`
(G-CONF), not by an axiom. The `datetime.datetime(...)` value constructor is not a
repo callee under spec; its effect is reproduced by the `Instant` record assembly.
There is no `opaque`/`axiom` callee whose contract the proof consumes.

There is therefore nothing for G-AX to validate. Exit 0 with status=skip.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "django__django-16429",
    "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
              "(pivot field assembly validated by G-CONF)",
}))
sys.exit(0)
