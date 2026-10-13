#!/usr/bin/env python3
"""G-AX skip stub for sympy__sympy-21612.

No consumed callee axiom is declared in the bundle and no deep-model A-reference
is axiomatized. The modeled routine (the denominator-factor bracketing branch of
`StrPrinter._print_Mul`) decides WHETHER a denominator factor's rendered base
fragment is wrapped in one extra pair of brackets, and splices the result into a
constant textual template. The base-fragment renderer (the printer's own
`self.parenthesize` dispatch) is left as a universally-quantified parameter
`render : Expr -> String` in Solution.lean — the spec holds for EVERY renderer, so
the proof consumes no property of it. There is no `opaque` callee and no `axiom
<callee>_prop` in Solution.lean, so there is nothing for G-AX to validate. The
bracketing-predicate + framing impl (and its binding to the REAL base renderer) is
differential-tested by conformance_check.py (G-CONF).

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "sympy__sympy-21612",
        "reason": "no consumed callee axiom and no axiomatized A-reference; the "
                  "base-fragment renderer is universally quantified, so the impl "
                  "is all R/I/A-reference (validated by G-CONF against the real "
                  "StrPrinter denominator-factor bracketing in _print_Mul)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
