#!/usr/bin/env python3
"""G-AX skip stub for django__django-13590.

No consumed callee axiom is declared in the bundle and no deep-model A-reference
is axiomatized. The modeled behavior (`Query.resolve_lookup_value`) is the
structural resolve-and-rebuild of a value. The resolution of a single expression
is left as a universally-quantified parameter `resolveExpr : Nat -> Value` in
Solution.lean — the spec holds for EVERY expression resolver — so the proof
consumes no property of it. There is no `opaque` callee and no
`axiom <callee>_prop` in Solution.lean, so there is nothing for G-AX to validate.
The rebuild impl (and its binding to the REAL patched `resolve_lookup_value`) is
differential-tested by conformance_check.py (G-CONF).

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "django__django-13590",
        "reason": "no consumed callee axiom and no axiomatized A-reference; the "
                  "single-expression resolver is universally quantified, so the "
                  "impl is all R/I/A-reference (validated by G-CONF against the "
                  "real patched Query.resolve_lookup_value)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
