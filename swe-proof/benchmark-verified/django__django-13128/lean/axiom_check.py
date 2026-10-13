#!/usr/bin/env python3
"""G-AX skip stub for django__django-13128.

No consumed callee axiom is declared in the bundle and no deep-model A-reference
is used. The modeled function (`CombinedExpression.resolve_expression`) is
modeled DEEPLY: the behavior the patch changes — the decision of which KIND a
resolved arithmetic combination becomes (ordinary / duration / temporal) — is
spelled out as a total function (`classifyKind`) of the combination's current
kind, the operator, and the two resolved operands' value-types. The operations
the dispatch consults (resolving operands, reading `output_field.get_internal_type()`,
the `isinstance` class test) are unchanged callees whose RESULTS are the modeled
inputs; none of their properties is consumed by the correctness proof, so there
is no callee-property contract for G-AX to validate.

The full R/I impl is differential-tested by conformance_check.py (G-CONF).

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "django__django-13128",
        "reason": "no consumed callee axiom and no A-reference; the changed "
                  "resolve-time classification decision is modeled deeply as a "
                  "total function of the operand value-types, operator, and "
                  "current expression kind; behavior validated by G-CONF",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
