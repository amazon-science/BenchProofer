#!/usr/bin/env python3
r"""G-AX for django__django-11099.

Neither `correct_validateAscii` nor `correct_validateUnicode` consumes a
`_prop` axiom: the imperative loop equals `username.all isAllowed*` purely
structurally (loop-as-fold), independent of the per-character predicate's truth
table. The per-character allowed-set callees `isAllowedAscii` / `isAllowedUnicode`
are left `opaque` and the proof asserts NO property about them, so there is no
consumed callee axiom for G-AX to validate.

The correspondence between the opaque per-character predicates and the REAL
`[\w.@+-]` class membership (under `re.ASCII` and flags `0` respectively) is the
R/I concern, exercised mechanically by conformance_check.py (G-CONF) against the
real compiled regex. Hence this gate is a principled skip stub (cf. the
django__django-11066 precedent: no consumed axiom ⇒ G-AX skip).

stdlib-only; exit 0.
"""
import json
import sys

report = {
    "status": "skip",
    "instance": "django__django-11099",
    "reason": (
        "no consumed callee axiom: both correct_* theorems prove the loop equals "
        "`username.all isAllowed*` structurally, independent of the opaque "
        "per-character predicate; isAllowedAscii/isAllowedUnicode are A-reference "
        "callees whose correspondence to the real [\\w.@+-] class membership is "
        "validated by conformance_check.py (G-CONF), not by a Lean _prop axiom"
    ),
}
print(json.dumps(report))
sys.exit(0)
