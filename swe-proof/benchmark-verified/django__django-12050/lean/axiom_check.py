#!/usr/bin/env python3
"""G-AX skip stub for django__django-12050.

The bundle declares one `opaque` callee, `resolveExpression`, modeling the
UNCHANGED `value.resolve_expression(self, **kwargs)` callee. It is an
A-REFERENCE with NO consumed property: it appears IDENTICALLY in the spec
helper `resolveSpec` (`LV.expr e => resolveExpression e`) and in
`implementation_resolveLookupValue` (`LV.expr e => resolveExpression e`), so it
cancels in the correctness argument — the proof needs no property of it. There
is therefore NO `axiom resolveExpression_prop` in Solution.lean for G-AX to
validate against the real callee.

The behavior the patch actually changes — preserving the input container type
(`type(value)(...)`) and recursing into every entry — is modeled DEEPLY in Lean
(`resolveSpec` / the recursive `implementation_resolveLookupValue`), an R/I leg,
and is mechanically differential-tested against an in-process replica of the
patched `resolve_lookup_value` by conformance_check.py (G-CONF).

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "django__django-12050",
        "reason": "the only opaque callee (resolveExpression / "
                  "value.resolve_expression) is an A-reference with no consumed "
                  "property — it cancels (identical in spec and impl), so there "
                  "is no axiom to validate. The changed behavior (container-type "
                  "preservation + recursion) is R/I, validated by G-CONF.",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
