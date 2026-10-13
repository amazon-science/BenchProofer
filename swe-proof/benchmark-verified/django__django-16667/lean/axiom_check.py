#!/usr/bin/env python3
"""G-AX skip stub for django__django-16667.

No consumed callee axiom is declared in the bundle and no deep-model A-reference
is axiomatized. The modeled behavior (the date-coercion try/except block of
`SelectDateWidget.value_from_datadict`) dispatches on the outcome of constructing
a calendar date from three raw components. The behavior the patch changes — what
the OverflowError outcome (a component too large to be a calendar component) hands
on — is modeled DEEPLY (`DateEntry.unrepresentable -> "0-0-0"`; SPEC_GUIDE §3: a
deeply-modeled changed decision is never axiomatized). The classification of the
entry into valid / malformed / unrepresentable is produced by the UNCHANGED
callees `int` and `datetime.date`; it enters the modeled computation as the input
`c : DateEntry`, and the canonical rendering of a representable date enters as the
input `rendered`. The proof consumes no property of any external callee: it only
dispatches on `c`. There is no `opaque` callee and no `axiom <callee>_prop` in
Solution.lean, so there is nothing for G-AX to validate. The binding of the
inputs to the real callees (and the whole R/I impl) is differential-tested by
conformance_check.py (G-CONF), which runs the real `int`/`datetime.date`/
`strftime`.

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main():
    print(json.dumps({
        "status": "skip",
        "instance": "django__django-16667",
        "reason": "no consumed callee axiom and no axiomatized A-reference; the "
                  "OverflowError-outcome value is modeled deeply "
                  "(DateEntry.unrepresentable -> \"0-0-0\") and the entry "
                  "classification / canonical rendering enter as inputs "
                  "(c / rendered), so the impl is all R/I (validated by G-CONF "
                  "against the real patched value_from_datadict coercion block)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
