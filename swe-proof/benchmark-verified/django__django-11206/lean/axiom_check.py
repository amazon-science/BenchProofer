#!/usr/bin/env python3
"""G-AX skip stub for django__django-11206.

No consumed callee axiom is declared in the bundle. The only modeled callee,
`renderDecimal` (the UNCHANGED value-to-string rendering tail of
`numberformat.format`), is declared `opaque` in Solution.lean but the proof
consumes NO property of it: `problem_spec_formatNumber` states `result =
renderDecimal (snapValue number decimalPos) …` and `implementation_formatNumber`
computes exactly that, so correctness is the structural identity of the snapped
argument — there is no `renderDecimal_prop` axiom for G-AX to validate.

`renderDecimal` is an A-reference: its binding to the REAL base-commit rendering
tail is exercised by conformance_check.py (G-CONF), which composes the modeled
smallness adjustment with the real renderer and differential-tests against the
real patched `format`.

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "django__django-11206",
        "reason": "no consumed callee axiom; the unchanged rendering tail "
                  "(renderDecimal) is an opaque A-reference of which the proof "
                  "consumes no property (both sides of problem_spec apply the "
                  "same renderer to the same snapped argument). Its binding to "
                  "the real rendering tail is validated by G-CONF.",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
